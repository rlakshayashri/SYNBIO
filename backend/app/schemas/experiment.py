import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.comparison import ComparisonResponse
from app.schemas.experimental_group import (
    ExperimentalGroupCreate,
    ExperimentalGroupResponse,
)


class ExperimentBase(BaseModel):
    """Base schema for Experiment data."""

    name: str = Field(..., min_length=1, max_length=255, description="Experiment title or identifier.")
    description: str | None = Field(default=None, description="Detailed experimental description.")
    organism: str | None = Field(default=None, max_length=100, description="Model organism or biological system.")
    condition_type: str | None = Field(
        default=None, max_length=100, description="Primary variable/condition type (e.g., temperature, concentration)."
    )
    notes: str | None = Field(default=None, description="Additional scientific notes or context.")


class ExperimentCreate(ExperimentBase):
    """Schema for creating an Experiment."""

    project_id: uuid.UUID = Field(..., description="ID of parent project.")
    dataset_id: uuid.UUID | None = Field(default=None, description="Optional associated dataset ID.")
    groups: list[ExperimentalGroupCreate] = Field(default_factory=list, description="Initial experimental groups.")


class ExperimentUpdate(BaseModel):
    """Schema for updating an Experiment."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    organism: str | None = Field(default=None, max_length=100)
    condition_type: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None)
    dataset_id: uuid.UUID | None = Field(default=None)


class ExperimentResponse(ExperimentBase):
    """Schema for Experiment response."""

    id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID | None = None
    groups: list[ExperimentalGroupResponse] = Field(default_factory=list)
    comparisons: list[ComparisonResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
