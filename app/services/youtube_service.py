import logging
import os
import re
from pathlib import Path

from yt_dlp import YoutubeDL

from app.core.exceptions import AppError


YOUTUBE_REGEX = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$", re.IGNORECASE)
LOGGER = logging.getLogger(__name__)


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
            "retries": 5,
            "fragment_retries": 5,
            "extractor_retries": 3,
            "socket_timeout": 15,
            "geo_bypass": True,
            "concurrent_fragment_downloads": 1,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web", "tv"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        cookie_file = os.getenv("YTDLP_COOKIEFILE")
        if cookie_file:
            options["cookiefile"] = cookie_file

        cookies_from_browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
        if cookies_from_browser:
            options["cookiesfrombrowser"] = tuple(
                part.strip() for part in cookies_from_browser.split(":") if part.strip()
            )

        try:
            with YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as exc:
            LOGGER.exception("Falha ao baixar áudio do YouTube: %s", exc)
            details = "Tente novamente em instantes"
            error_message = str(exc).lower()
            blocked_by_bot_check = "sign in to confirm you're not a bot" in error_message or "sign in to confirm you’re not a bot" in error_message
            if blocked_by_bot_check:
                details = (
                    "O YouTube exigiu verificação anti-bot para esta URL. "
                    "Configure YTDLP_COOKIEFILE ou YTDLP_COOKIES_FROM_BROWSER "
                    "com uma sessão válida e tente novamente"
                )
            elif cookie_file:
                details += " e valide o arquivo YTDLP_COOKIEFILE"
            else:
                details += " ou configure YTDLP_COOKIEFILE para vídeos com restrição"
            raise AppError(
                "YOUTUBE_DOWNLOAD_FAILED",
                f"Falha ao baixar áudio do YouTube ({details}).",
                status_code=502,
            ) from exc

        files = sorted(output_dir.glob("youtube.*"))
        if not files:
            raise AppError("YOUTUBE_DOWNLOAD_FAILED", "Arquivo de áudio do YouTube não foi gerado.", status_code=502)
        return files[0]
