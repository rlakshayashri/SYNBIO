import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.replicate import ReplicateCreate, ReplicateResponse


class ExperimentalGroupBase(BaseModel):
    """Base schema for ExperimentalGroup data."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name of experimental group.")
    group_code: str = Field(..., min_length=1, max_length=50, description="Short code matching data category.")
    is_control: bool = Field(default=False, description="Flag indicating if group is a control condition.")
    description: str | None = Field(default=None, description="Detailed description of treatment/condition.")
    metadata_payload: dict[str, Any] = Field(default_factory=dict, description="Structured group metadata.")


class ExperimentalGroupCreate(ExperimentalGroupBase):
    """Schema for creating an ExperimentalGroup."""

    replicates: list[ReplicateCreate] = Field(default_factory=list, description="Optional initial list of replicates.")


class ExperimentalGroupUpdate(BaseModel):
    """Schema for updating an ExperimentalGroup."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    group_code: str | None = Field(default=None, min_length=1, max_length=50)
    is_control: bool | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_payload: dict[str, Any] | None = Field(default=None)


class ExperimentalGroupResponse(ExperimentalGroupBase):
    """Schema for ExperimentalGroup response."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    replicates: list[ReplicateResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
