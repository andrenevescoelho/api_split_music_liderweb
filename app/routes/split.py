from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.core.config import get_settings
from app.core.deps import get_split_service
from app.core.exceptions import AppError
from app.schemas.split import SplitResponse, YoutubeSplitRequest
from app.services.split_service import SplitService

router = APIRouter(prefix="/split", tags=["split"])


@router.post("/upload", response_model=SplitResponse)
async def split_upload(
    request: Request,
    file: UploadFile = File(...),
    split_service: SplitService = Depends(get_split_service),
):
    settings = get_settings()
    body = await file.read(settings.max_upload_bytes + 1)
    if len(body) > settings.max_upload_bytes:
        raise AppError("FILE_TOO_LARGE", f"Arquivo excede {settings.max_upload_mb}MB.", status_code=413)

    if settings.api_key:
        incoming = request.headers.get("x-api-key")
        if incoming != settings.api_key:
            raise AppError("UNAUTHORIZED", "API key inválida.", status_code=401)

    return split_service.process_upload(body, file.filename or "audio.mp3", file.content_type)


@router.post("/youtube", response_model=SplitResponse)
def split_youtube(
    payload: YoutubeSplitRequest,
    request: Request,
    split_service: SplitService = Depends(get_split_service),
):
    settings = get_settings()

    if settings.api_key:
        incoming = request.headers.get("x-api-key")
        if incoming != settings.api_key:
            raise AppError("UNAUTHORIZED", "API key inválida.", status_code=401)

    return split_service.process_youtube(str(payload.url), settings.ytdlp_enabled)


@router.get("/result/{job_id}")
def get_split_result(job_id: str, split_service: SplitService = Depends(get_split_service)):
    return split_service.get_result(job_id)
