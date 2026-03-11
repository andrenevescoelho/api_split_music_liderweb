from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np

from app.analysis.helpers import clamp_confidence

logger = logging.getLogger(__name__)

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Schmuckler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


class KeyAnalyzer:
    def analyze(self, audio_path: Path) -> tuple[str | None, str | None, float]:
        try:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
            if y.size == 0:
                return None, None, 0.0

            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            if chroma.size == 0:
                return None, None, 0.0

            chroma_mean = np.mean(chroma, axis=1)
            chroma_mean = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-9)

            major_scores = [self._corr(chroma_mean, np.roll(MAJOR_PROFILE, i)) for i in range(12)]
            minor_scores = [self._corr(chroma_mean, np.roll(MINOR_PROFILE, i)) for i in range(12)]

            best_major_idx = int(np.argmax(major_scores))
            best_minor_idx = int(np.argmax(minor_scores))
            best_major_score = float(major_scores[best_major_idx])
            best_minor_score = float(minor_scores[best_minor_idx])

            if best_major_score >= best_minor_score:
                key, mode, best = KEY_NAMES[best_major_idx], "major", best_major_score
                second_best = max(best_minor_score, self._second_best(major_scores, best_major_idx))
            else:
                key, mode, best = KEY_NAMES[best_minor_idx], "minor", best_minor_score
                second_best = max(best_major_score, self._second_best(minor_scores, best_minor_idx))

            margin = max(0.0, best - second_best)
            confidence = clamp_confidence(0.5 + margin)
            return key, mode, confidence
        except Exception:
            logger.exception("Key analysis failed for %s", audio_path)
            return None, None, 0.0

    def _corr(self, chroma_vector: np.ndarray, profile: np.ndarray) -> float:
        profile_norm = profile / (np.linalg.norm(profile) + 1e-9)
        return float(np.dot(chroma_vector, profile_norm))

    def _second_best(self, scores: list[float], best_idx: int) -> float:
        copy = [score for i, score in enumerate(scores) if i != best_idx]
        return float(max(copy)) if copy else 0.0
