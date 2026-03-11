from __future__ import annotations

import logging
from pathlib import Path

from app.analysis.bpm_analyzer import BpmAnalyzer
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
        bpm_candidates = self._build_candidates(stem_paths, ["drums", "percussion"], original_audio)
        key_candidates = self._build_candidates(stem_paths, ["other", "piano", "guitar", "keys", "pads"], original_audio)

        bpm_stem_name, bpm, display_bpm, bpm_conf = self._analyze_bpm_with_fallback(bpm_candidates)
        key_stem_name, key_input, key, mode, key_conf = self._analyze_key_with_fallback(key_candidates)
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

    def _build_candidates(
        self,
        stem_paths: dict[str, Path],
        preferred_stems: list[str],
        original_audio: Path,
    ) -> list[tuple[str, Path]]:
        candidates: list[tuple[str, Path]] = []
        for stem in preferred_stems:
            path = stem_paths.get(stem)
            if path and path.exists():
                candidates.append((stem, path))

        candidates.append(("mix", original_audio))
        return candidates

    def _analyze_bpm_with_fallback(self, candidates: list[tuple[str, Path]]) -> tuple[str, int | None, int | None, float]:
        for stem_name, audio_path in candidates:
            bpm, display_bpm, bpm_conf = self.bpm_analyzer.analyze(audio_path)
            if bpm is not None:
                return stem_name, bpm, display_bpm, bpm_conf

        return candidates[-1][0], None, None, 0.0

    def _analyze_key_with_fallback(
        self,
        candidates: list[tuple[str, Path]],
    ) -> tuple[str, Path, str | None, str | None, float]:
        for stem_name, audio_path in candidates:
            key, mode, key_conf = self.key_analyzer.analyze(audio_path)
            if key is not None:
                return stem_name, audio_path, key, mode, key_conf

        fallback_stem_name, fallback_path = candidates[-1]
        return fallback_stem_name, fallback_path, None, None, 0.0
