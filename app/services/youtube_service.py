from app.core.exceptions import AppError


class YoutubeService:
    def validate_url(self, url: str) -> None:
        raise AppError("YOUTUBE_DISABLED", "Integração com YouTube foi removida.", status_code=410)

    def download_audio(self, url: str, output_dir):
        raise AppError("YOUTUBE_DISABLED", "Integração com YouTube foi removida.", status_code=410)
