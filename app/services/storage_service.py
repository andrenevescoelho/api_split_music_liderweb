from abc import ABC, abstractmethod
from pathlib import Path


class StorageService(ABC):
    @abstractmethod
    def ensure_directories(self) -> None:
        ...

    @abstractmethod
    def create_job_dir(self, job_id: str) -> Path:
        ...

    @abstractmethod
    def job_path(self, job_id: str) -> Path:
        ...

    @abstractmethod
    def public_url(self, relative_path: str) -> str:
        ...
