from functools import lru_cache

from app.core.config import get_settings
from app.services.audio_processing_service import AudioProcessingService
from app.services.local_storage_service import LocalStorageService
from app.services.split_service import SplitService
from app.services.youtube_service import YoutubeService


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
        youtube_service=YoutubeService(),
    )
