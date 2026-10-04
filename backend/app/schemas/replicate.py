import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReplicateBase(BaseModel):
    """Base schema for Replicate data."""

    replicate_name: str = Field(..., min_length=1, max_length=255, description="Name or identifier of the replicate.")
    sample_identifier: str | None = Field(default=None, max_length=255, description="Optional original sample ID.")
    row_index: int | None = Field(default=None, description="Optional row index in the raw dataset.")
    replicate_type: str = Field(default="biological", description="Type of replicate (biological, technical).")
    metadata_payload: dict[str, Any] = Field(default_factory=dict, description="Arbitrary experimental metadata.")


class ReplicateCreate(ReplicateBase):
    """Schema for creating a Replicate."""

    pass


class ReplicateUpdate(BaseModel):
    """Schema for updating a Replicate."""

    replicate_name: str | None = Field(default=None, min_length=1, max_length=255)
    sample_identifier: str | None = Field(default=None, max_length=255)
    row_index: int | None = Field(default=None)
    replicate_type: str | None = Field(default=None)
    metadata_payload: dict[str, Any] | None = Field(default=None)


class ReplicateResponse(ReplicateBase):
    """Schema for Replicate response."""

    id: uuid.UUID
    group_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
