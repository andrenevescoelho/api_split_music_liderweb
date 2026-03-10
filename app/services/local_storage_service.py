from pathlib import Path

from app.core.config import Settings
from app.services.storage_service import StorageService


class LocalStorageService(StorageService):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage_dir = Path(settings.storage_dir)
        self.temp_dir = Path(settings.temp_dir)
        self.output_dir = Path(settings.output_dir)

    def ensure_directories(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_job_dir(self, job_id: str) -> Path:
        job_dir = self.output_dir / job_id
        (job_dir / "stems").mkdir(parents=True, exist_ok=True)
        return job_dir

    def job_path(self, job_id: str) -> Path:
        return self.output_dir / job_id

    def public_url(self, relative_path: str) -> str:
        base = self.settings.base_url.rstrip("/")
        rel = relative_path.lstrip("/")
        return f"{base}/files/{rel}"
