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


class BpmAnalyzer:
    """Beat tracking based BPM estimator using librosa DSP."""

    def analyze(self, audio_path: Path) -> tuple[int | None, int | None, float]:
        if librosa is None:
            logger.warning("Skipping BPM analysis for %s: librosa is not installed", audio_path)
            return None, None, 0.0

        try:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
            if y.size == 0:
                return None, None, 0.0

            tempo_arr, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
            bpm = float(np.ravel(tempo_arr)[0]) if np.size(tempo_arr) else 0.0
            if bpm <= 0:
                return None, None, 0.0

            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            confidence = self._beat_confidence(beat_times)
            bpm_rounded = int(round(bpm))
            display_bpm = self._display_bpm(bpm_rounded)
            return bpm_rounded, display_bpm, clamp_confidence(confidence)
        except Exception as exc:
            logger.exception("BPM analysis failed for %s", audio_path)
            return None, None, 0.0

    def _display_bpm(self, bpm: int) -> int:
        # Heurística musical para half/double-time em faixas populares.
        if bpm >= 140:
            return int(round(bpm / 2))
        if bpm <= 70:
            return int(round(bpm * 2))
        return bpm

    def _beat_confidence(self, beat_times: np.ndarray) -> float:
        if beat_times.size < 4:
            return 0.2

        intervals = np.diff(beat_times)
        mean_interval = float(np.mean(intervals))
        if mean_interval <= 0:
            return 0.1

        cv = float(np.std(intervals) / mean_interval)
        density_bonus = min(0.3, beat_times.size / 300.0)
        confidence = (1.0 - min(cv, 1.0)) * 0.7 + density_bonus
        return confidence
