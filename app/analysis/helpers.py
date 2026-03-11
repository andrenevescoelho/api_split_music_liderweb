from __future__ import annotations

from pathlib import Path


def pick_existing_stem(stem_paths: dict[str, Path], preferred_order: list[str]) -> tuple[str, Path] | None:
    for stem_name in preferred_order:
        stem_path = stem_paths.get(stem_name)
        if stem_path and stem_path.exists():
            return stem_name, stem_path
    return None


def clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
