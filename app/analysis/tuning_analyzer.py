from __future__ import annotations

import logging
from pathlib import Path

try:
    import librosa
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    librosa = None

logger = logging.getLogger(__name__)


class TuningAnalyzer:
    def analyze(self, audio_path: Path) -> float | None:
        if librosa is None:
            logger.warning("Skipping tuning analysis for %s: librosa is not installed", audio_path)
            return None

        try:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
            if y.size == 0:
                return None

            tuning_fraction = float(librosa.estimate_tuning(y=y, sr=sr))
            tuning_hz = 440.0 * (2.0 ** (tuning_fraction / 12.0))
            return round(float(tuning_hz), 2)
        except Exception:
            logger.exception("Tuning analysis failed for %s", audio_path)
            return None
