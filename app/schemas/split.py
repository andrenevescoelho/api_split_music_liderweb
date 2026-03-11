from typing import Dict, Optional

from pydantic import BaseModel, Field


class ProcessingMetadata(BaseModel):
    filename: str
    duration_seconds: Optional[float] = None
    processing_time_seconds: float


class AnalysisConfidence(BaseModel):
    bpm: float = 0.0
    key: float = 0.0


class AnalysisResult(BaseModel):
    bpm: int | None = None
    display_bpm: int | None = Field(default=None, alias="displayBpm")
    key: str | None = None
    mode: str | None = None
    tuning_hz: float | None = Field(default=None, alias="tuningHz")
    confidence: AnalysisConfidence = Field(default_factory=AnalysisConfidence)
    sources: Dict[str, str] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class SplitResponse(BaseModel):
    success: bool = True
    status: str = "completed"
    job_id: str
    source_type: str
    original_audio_url: str
    stems: Dict[str, str]
    metadata: ProcessingMetadata
    analysis: AnalysisResult | None = None


class HealthResponse(BaseModel):
    success: bool = True
    status: str = "ok"
