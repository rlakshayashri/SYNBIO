from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Base schema with common Project attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the project")
    description: str | None = Field(None, description="Optional detailed description")


class ProjectCreate(ProjectBase):
    """Schema for creating a new Project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing Project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(ProjectBase):
    """Schema for Project responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
