from typing import Dict, Optional

from pydantic import BaseModel


class ProcessingMetadata(BaseModel):
    filename: str
    duration_seconds: Optional[float] = None
    processing_time_seconds: float


class SplitResponse(BaseModel):
    success: bool = True
    job_id: str
    source_type: str
    original_audio_url: str
    stems: Dict[str, str]
    metadata: ProcessingMetadata


class HealthResponse(BaseModel):
    success: bool = True
    status: str = "ok"
