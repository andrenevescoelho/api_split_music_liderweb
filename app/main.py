from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.deps import get_storage_service
from app.core.exceptions import AppError
from app.routes.health import router as health_router
from app.routes.split import router as split_router
from app.schemas.common import ErrorData, ErrorResponse

settings = get_settings()
storage = get_storage_service()

app = FastAPI(
    title="Music Split API",
    description="API local para split de música via upload ou YouTube usando Demucs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    payload = ErrorResponse(error=ErrorData(code=exc.code, message=exc.message))
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception):
    payload = ErrorResponse(error=ErrorData(code="INTERNAL_ERROR", message="Erro interno do servidor."))
    return JSONResponse(status_code=500, content=payload.model_dump())


app.include_router(health_router)
app.include_router(split_router)
app.mount("/files", StaticFiles(directory=settings.storage_dir), name="files")
