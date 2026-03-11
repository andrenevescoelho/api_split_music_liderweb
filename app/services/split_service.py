import logging
import time
import uuid
from pathlib import Path

from app.core.exceptions import AppError
from app.schemas.split import AnalysisResult, ProcessingMetadata, SplitResponse
from app.services.audio_processing_service import AudioProcessingService
from app.services.local_storage_service import LocalStorageService
from app.analysis.music_analyzer import MusicAnalyzer
from app.utils.files import sanitize_filename, validate_upload

logger = logging.getLogger(__name__)


class SplitService:
    def __init__(
        self,
        storage_service: LocalStorageService,
        audio_service: AudioProcessingService,
        music_analyzer: MusicAnalyzer,
    ):
        self.storage = storage_service
        self.audio = audio_service
        self.music_analyzer = music_analyzer

    def _build_urls(self, job_id: str, stem_paths: dict[str, Path]) -> dict[str, str]:
        urls = {}
        for stem, path in stem_paths.items():
            relative = f"jobs/{job_id}/stems/{path.name}"
            urls[stem] = self.storage.public_url(relative)
        return urls

    def process_local_audio(self, source_type: str, input_path: Path, original_name: str, job_id: str | None = None) -> SplitResponse:
        started = time.perf_counter()
        job_id = job_id or uuid.uuid4().hex[:12]
        job_dir = self.storage.create_job_dir(job_id)

        original_ext = input_path.suffix.lower() or ".mp3"
        original_file = job_dir / f"original{original_ext}"
        input_path.replace(original_file)

        wav_input = job_dir / "internal.wav"
        self.audio.convert_to_internal_wav(original_file, wav_input)

        stems_raw_dir = self.audio.split_with_demucs(wav_input, job_dir)
        stem_paths = self.audio.convert_stems_to_mp3(stems_raw_dir, job_dir / "stems")

        analysis_result = self._safe_analyze(original_file, stem_paths)

        processing_time = round(time.perf_counter() - started, 2)
        duration = self.audio.duration_seconds(original_file)

        response = SplitResponse(
            job_id=job_id,
            source_type=source_type,
            original_audio_url=self.storage.public_url(f"jobs/{job_id}/{original_file.name}"),
            stems=self._build_urls(job_id, stem_paths),
            metadata=ProcessingMetadata(
                filename=original_name,
                duration_seconds=duration,
                processing_time_seconds=processing_time,
            ),
            analysis=analysis_result,
        )

        self.audio.write_result_manifest(job_dir, response.model_dump(by_alias=True))
        self.audio.cleanup_temp(job_dir)
        if wav_input.exists():
            wav_input.unlink(missing_ok=True)
        return response

    def process_upload(self, file_bytes: bytes, filename: str, content_type: str | None) -> SplitResponse:
        validate_upload(filename, content_type)
        safe_name = sanitize_filename(filename)
        tmp_input = Path(self.storage.temp_dir) / f"{uuid.uuid4().hex}_{safe_name}"
        tmp_input.write_bytes(file_bytes)
        return self.process_local_audio("upload", tmp_input, safe_name)

    def get_result(self, job_id: str) -> dict:
        result_file = self.storage.job_path(job_id) / "result.json"
        if not result_file.exists():
            raise AppError("JOB_NOT_FOUND", "Job não encontrado.", status_code=404)
        import json

        return json.loads(result_file.read_text(encoding="utf-8"))

    def _safe_analyze(self, original_file: Path, stem_paths: dict[str, Path]) -> AnalysisResult | None:
        try:
            return self.music_analyzer.analyze(original_file, stem_paths)
        except Exception:
            logger.exception("Music analysis failed; split output will still be returned")
            return None
