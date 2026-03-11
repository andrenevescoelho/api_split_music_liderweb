from __future__ import annotations

import logging
from pathlib import Path

from app.analysis.bpm_analyzer import BpmAnalyzer
from app.analysis.helpers import pick_existing_stem
from app.analysis.key_analyzer import KeyAnalyzer
from app.analysis.tuning_analyzer import TuningAnalyzer
from app.schemas.split import AnalysisConfidence, AnalysisResult

logger = logging.getLogger(__name__)


class MusicAnalyzer:
    def __init__(
        self,
        bpm_analyzer: BpmAnalyzer | None = None,
        key_analyzer: KeyAnalyzer | None = None,
        tuning_analyzer: TuningAnalyzer | None = None,
    ):
        self.bpm_analyzer = bpm_analyzer or BpmAnalyzer()
        self.key_analyzer = key_analyzer or KeyAnalyzer()
        self.tuning_analyzer = tuning_analyzer or TuningAnalyzer()

    def analyze(self, original_audio: Path, stem_paths: dict[str, Path]) -> AnalysisResult:
        bpm_source = pick_existing_stem(stem_paths, ["drums", "percussion"])
        key_source = pick_existing_stem(stem_paths, ["other", "piano", "guitar", "keys", "pads"])

        bpm_stem_name, bpm_input = (bpm_source if bpm_source else ("mix", original_audio))
        key_stem_name, key_input = (key_source if key_source else ("mix", original_audio))

        bpm, display_bpm, bpm_conf = self.bpm_analyzer.analyze(bpm_input)
        key, mode, key_conf = self.key_analyzer.analyze(key_input)
        tuning_hz = self.tuning_analyzer.analyze(key_input)

        logger.info(
            "Music analysis finished | bpm=%s display_bpm=%s key=%s mode=%s tuning_hz=%s bpm_src=%s key_src=%s",
            bpm,
            display_bpm,
            key,
            mode,
            tuning_hz,
            bpm_stem_name,
            key_stem_name,
        )

        return AnalysisResult(
            bpm=bpm,
            display_bpm=display_bpm,
            key=key,
            mode=mode,
            tuning_hz=tuning_hz,
            confidence=AnalysisConfidence(bpm=round(bpm_conf, 3), key=round(key_conf, 3)),
            sources={"bpm": bpm_stem_name, "key": key_stem_name},
        )
