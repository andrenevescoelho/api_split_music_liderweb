from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

try:
    import librosa
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    librosa = None

from app.analysis.helpers import clamp_confidence

logger = logging.getLogger(__name__)

# BPM range considered musically valid
BPM_MIN = 60
BPM_MAX = 200


class BpmAnalyzer:
    """
    Multi-method BPM estimator using librosa DSP.

    Strategy:
      1. Segment the audio into 3 overlapping windows and estimate BPM per
         window using beat_track (onset-envelope based). This avoids a single
         bad segment skewing the result.
      2. Estimate tempo independently via the tempogram (autocorrelation of
         the onset envelope) — more robust to irregular rhythms.
      3. Collect all candidate BPMs, snap them to a common grid (round to
         nearest 0.5 BPM) and pick the value with the most votes.
      4. Confidence is derived from the agreement between methods and the
         regularity of the detected beat intervals.
    """

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(self, audio_path: Path) -> tuple[int | None, int | None, float]:
        if librosa is None:
            logger.warning("Skipping BPM analysis for %s: librosa is not installed", audio_path)
            return None, None, 0.0

        try:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
            if y.size == 0:
                return None, None, 0.0

            candidates: list[float] = []

            # --- Method 1: windowed beat_track ---
            window_bpms, beat_times_global = self._windowed_beat_track(y, sr)
            candidates.extend(window_bpms)

            # --- Method 2: tempogram-based tempo ---
            tg_bpms = self._tempogram_tempo(y, sr)
            candidates.extend(tg_bpms)

            # --- Method 3: full-signal beat_track as tie-breaker ---
            full_bpm = self._full_beat_track(y, sr)
            if full_bpm is not None:
                candidates.append(full_bpm)

            valid = [b for b in candidates if BPM_MIN <= b <= BPM_MAX]
            if not valid:
                logger.warning("No valid BPM candidates for %s (raw=%s)", audio_path, candidates)
                return None, None, 0.0

            bpm_float, confidence = self._vote(valid, beat_times_global)
            bpm_rounded = int(round(bpm_float))
            display_bpm = self._display_bpm(bpm_rounded)

            logger.debug(
                "BPM analysis %s | candidates=%s → bpm=%s conf=%.3f",
                audio_path.name,
                [round(b, 1) for b in valid],
                bpm_rounded,
                confidence,
            )

            return bpm_rounded, display_bpm, clamp_confidence(confidence)

        except Exception:
            logger.exception("BPM analysis failed for %s", audio_path)
            return None, None, 0.0

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _windowed_beat_track(
        self, y: np.ndarray, sr: int, n_windows: int = 3
    ) -> tuple[list[float], np.ndarray]:
        """Run beat_track on overlapping segments; return per-window BPMs and
        a merged array of beat times for the whole signal."""
        total_samples = len(y)
        # Use 60 s windows with 50 % overlap, capped to signal length
        win_samples = min(int(60 * sr), total_samples)
        step = max(win_samples // 2, 1)

        starts = list(range(0, max(total_samples - win_samples + 1, 1), step))[:n_windows]

        bpms: list[float] = []
        all_beat_times: list[np.ndarray] = []

        for start in starts:
            segment = y[start : start + win_samples]
            tempo_arr, beat_frames = librosa.beat.beat_track(y=segment, sr=sr, units="frames")
            bpm = float(np.ravel(tempo_arr)[0]) if np.size(tempo_arr) else 0.0
            if BPM_MIN <= bpm <= BPM_MAX:
                bpms.append(bpm)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr) + start / sr
            all_beat_times.append(beat_times)

        merged_beats = np.concatenate(all_beat_times) if all_beat_times else np.array([])
        return bpms, merged_beats

    def _tempogram_tempo(self, y: np.ndarray, sr: int) -> list[float]:
        """Estimate BPM via onset-envelope autocorrelation (tempogram)."""
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
        # librosa.beat.tempo returns an array of tempo estimates
        tempo_arr = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, ac_size=8.0)
        return [float(t) for t in np.ravel(tempo_arr) if BPM_MIN <= float(t) <= BPM_MAX]

    def _full_beat_track(self, y: np.ndarray, sr: int) -> float | None:
        """Standard full-signal beat_track as an extra data point."""
        tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        bpm = float(np.ravel(tempo_arr)[0]) if np.size(tempo_arr) else 0.0
        return bpm if BPM_MIN <= bpm <= BPM_MAX else None

    def _vote(self, candidates: list[float], beat_times: np.ndarray) -> tuple[float, float]:
        """
        Snap all candidates to a 0.5-BPM grid and pick the most-voted bucket.
        Confidence blends vote agreement with beat-interval regularity.
        """
        grid = 0.5
        snapped = [round(b / grid) * grid for b in candidates]

        # Count votes per bucket
        unique, counts = np.unique(snapped, return_counts=True)
        best_idx = int(np.argmax(counts))
        winner = float(unique[best_idx])
        vote_agreement = float(counts[best_idx]) / len(snapped)

        # Beat regularity bonus
        regularity = self._beat_regularity(beat_times)

        confidence = vote_agreement * 0.6 + regularity * 0.4
        return winner, confidence

    def _beat_regularity(self, beat_times: np.ndarray) -> float:
        """Coefficient-of-variation based regularity score ∈ [0, 1]."""
        if beat_times.size < 4:
            return 0.2
        intervals = np.diff(np.sort(beat_times))
        mean_iv = float(np.mean(intervals))
        if mean_iv <= 0:
            return 0.1
        cv = float(np.std(intervals) / mean_iv)
        density_bonus = min(0.2, beat_times.size / 400.0)
        return min(1.0, (1.0 - min(cv, 1.0)) * 0.8 + density_bonus)

    def _display_bpm(self, bpm: int) -> int:
        """Heurística musical para half/double-time em faixas populares."""
        if bpm >= 140:
            return int(round(bpm / 2))
        if bpm <= 70:
            return int(round(bpm * 2))
        return bpm
