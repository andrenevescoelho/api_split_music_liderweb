from app.services.storage_service import StorageService


class GCSStorageService(StorageService):
    """Placeholder for future GCP migration."""

    def ensure_directories(self) -> None:
        raise NotImplementedError("GCS storage will be implemented in phase 3.")

    def create_job_dir(self, job_id: str):
        raise NotImplementedError("GCS storage will be implemented in phase 3.")

    def job_path(self, job_id: str):
        raise NotImplementedError("GCS storage will be implemented in phase 3.")

    def public_url(self, relative_path: str) -> str:
        raise NotImplementedError("GCS storage will be implemented in phase 3.")
