import json
import shutil
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import AppError


class AudioProcessingService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _run(self, cmd: list[str], error_code: str, error_message: str) -> None:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip()
            raise AppError(error_code, f"{error_message}. Detalhe: {detail}", status_code=500) from exc

    def convert_to_internal_wav(self, input_path: Path, output_path: Path) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-ar",
            "44100",
            "-ac",
            "2",
            str(output_path),
        ]
        self._run(cmd, "FFMPEG_FAILED", "Falha na conversão de áudio")

    def duration_seconds(self, input_path: Path) -> float | None:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return round(float(result.stdout.strip()), 2)
        except Exception:
            return None

    def split_with_demucs(self, wav_input_path: Path, job_dir: Path) -> Path:
        demucs_out = job_dir / "demucs_raw"
        cmd = [
            "python",
            "-m",
            "demucs.separate",
            "--name",
            self.settings.demucs_model,
            "--out",
            str(demucs_out),
            str(wav_input_path),
        ]
        self._run(cmd, "DEMUCS_FAILED", "Falha no split com Demucs")

        model_dir = demucs_out / self.settings.demucs_model
        if not model_dir.exists():
            raise AppError("DEMUCS_OUTPUT_MISSING", "Saída do Demucs não encontrada.", status_code=500)

        dirs = [d for d in model_dir.iterdir() if d.is_dir()]
        if not dirs:
            raise AppError("DEMUCS_OUTPUT_MISSING", "Nenhum diretório de stems encontrado.", status_code=500)
        return dirs[0]

    def convert_stems_to_mp3(self, stems_source_dir: Path, stems_target_dir: Path) -> dict[str, Path]:
        output: dict[str, Path] = {}
        for stem in ["vocals", "drums", "bass", "other"]:
            wav_path = stems_source_dir / f"{stem}.wav"
            demucs_mp3_path = stems_source_dir / f"{stem}.mp3"
            if not wav_path.exists() and not demucs_mp3_path.exists():
                continue

            mp3_path = stems_target_dir / f"{stem}.mp3"
            if demucs_mp3_path.exists():
                shutil.copyfile(demucs_mp3_path, mp3_path)
                output[stem] = mp3_path
                continue

            cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)]
            self._run(cmd, "FFMPEG_FAILED", f"Falha ao converter stem {stem}")
            output[stem] = mp3_path

        if not output:
            raise AppError("STEMS_MISSING", "Nenhum stem foi gerado.", status_code=500)
        return output

    def cleanup_temp(self, job_dir: Path) -> None:
        raw = job_dir / "demucs_raw"
        if raw.exists():
            shutil.rmtree(raw, ignore_errors=True)

    def write_result_manifest(self, job_dir: Path, payload: dict) -> None:
        (job_dir / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
