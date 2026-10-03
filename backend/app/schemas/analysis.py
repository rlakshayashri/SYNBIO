from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisBase(BaseModel):
    """Base schema with common Analysis attributes."""

    analysis_type: str = Field(..., min_length=1, max_length=100, description="Type of scientific analysis")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Analysis input parameters")
    result: dict[str, Any] = Field(default_factory=dict, description="Analysis output results")
    software_version: str = Field("0.1.0", description="Version of scientific software engine")


class AnalysisCreate(AnalysisBase):
    """Schema for registering an Analysis run."""

    dataset_id: UUID


class AnalysisUpdate(BaseModel):
    """Schema for updating Analysis result or parameters."""

    result: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None


class AnalysisResponse(AnalysisBase):
    """Schema for Analysis responses."""

    id: UUID
    dataset_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
