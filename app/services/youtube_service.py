import re
from pathlib import Path

from yt_dlp import YoutubeDL

from app.core.exceptions import AppError


YOUTUBE_REGEX = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$", re.IGNORECASE)


class YoutubeService:
    def validate_url(self, url: str) -> None:
        if not YOUTUBE_REGEX.match(url):
            raise AppError("INVALID_YOUTUBE_URL", "URL do YouTube inválida.", status_code=400)

    def download_audio(self, url: str, output_dir: Path) -> Path:
        outtmpl = str(output_dir / "youtube.%(ext)s")
        options = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        try:
            with YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as exc:
            raise AppError("YOUTUBE_DOWNLOAD_FAILED", "Falha ao baixar áudio do YouTube.", status_code=502) from exc

        files = sorted(output_dir.glob("youtube.*"))
        if not files:
            raise AppError("YOUTUBE_DOWNLOAD_FAILED", "Arquivo de áudio do YouTube não foi gerado.", status_code=502)
        return files[0]
