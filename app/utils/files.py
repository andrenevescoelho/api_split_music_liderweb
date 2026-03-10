import re
from pathlib import Path

from app.core.exceptions import AppError

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/x-flac",
    "audio/mp4",
    "audio/x-m4a",
}


def sanitize_filename(filename: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(filename).name)
    return safe or "audio.mp3"


def validate_upload(filename: str, content_type: str | None) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError("INVALID_FILE", "Formato de arquivo não suportado.", status_code=400)

    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise AppError("INVALID_MIME", "MIME type de arquivo não suportado.", status_code=400)
