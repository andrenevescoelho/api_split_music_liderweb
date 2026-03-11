from functools import lru_cache

from fastapi import Depends
from fastapi.security import APIKeyHeader

from app.analysis.music_analyzer import MusicAnalyzer
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.audio_processing_service import AudioProcessingService
from app.services.local_storage_service import LocalStorageService
from app.services.split_service import SplitService

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


@lru_cache
def get_storage_service() -> LocalStorageService:
    storage = LocalStorageService(get_settings())
    storage.ensure_directories()
    return storage


@lru_cache
def get_split_service() -> SplitService:
    settings = get_settings()
    return SplitService(
        storage_service=get_storage_service(),
        audio_service=AudioProcessingService(settings),
        music_analyzer=MusicAnalyzer(),
    )


def require_api_key(incoming_api_key: str | None = Depends(api_key_header)) -> None:
    settings = get_settings()
    if not settings.api_key:
        return

    if incoming_api_key != settings.api_key:
        raise AppError("UNAUTHORIZED", "API key inválida.", status_code=401)
