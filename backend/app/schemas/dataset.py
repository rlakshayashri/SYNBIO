from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetBase(BaseModel):
    """Base schema with common Dataset attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Dataset display name")
    file_name: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_type: str = Field(..., description="MIME type or file extension (csv, xlsx)")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    row_count: int | None = Field(None, ge=0, description="Total row count")
    column_count: int | None = Field(None, ge=0, description="Total column count")
    storage_path: str = Field(..., description="Path where file is stored")


class DatasetCreate(DatasetBase):
    """Schema for creating a Dataset record."""

    project_id: UUID


class DatasetUpdate(BaseModel):
    """Schema for updating Dataset metadata."""

    name: str | None = Field(None, min_length=1, max_length=255)
    row_count: int | None = Field(None, ge=0)
    column_count: int | None = Field(None, ge=0)


class DatasetResponse(DatasetBase):
    """Schema for Dataset responses."""

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ColumnMetadata(BaseModel):
    """Metadata summary for a single column."""

    name: str
    dtype: str
    null_count: int
    null_percentage: float


class DatasetPreviewResponse(BaseModel):
    """Structured response for dataset head preview."""

    dataset_id: UUID
    row_count: int
    column_count: int
    preview_rows: int
    columns: list[ColumnMetadata]
    data: list[dict[str, Any]]
