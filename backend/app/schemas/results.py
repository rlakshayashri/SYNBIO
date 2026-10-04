import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetProvenanceSummary(BaseModel):
    """Dataset metadata for result provenance."""

    id: uuid.UUID
    name: str
    file_name: str

    model_config = ConfigDict(from_attributes=True)


class ExperimentProvenanceSummary(BaseModel):
    """Experiment metadata for result provenance."""

    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class ComparisonProvenanceSummary(BaseModel):
    """Comparison metadata for result provenance."""

    id: uuid.UUID
    name: str
    comparison_type: str
    group_a_name: str | None = None
    group_b_name: str | None = None
    group_column: str | None = None
    measurement_column: str
    method: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ResultProvenance(BaseModel):
    """Explicit provenance chain tracking source relationships."""

    experiment_id: uuid.UUID
    dataset_id: uuid.UUID
    analysis_id: uuid.UUID
    comparison_id: uuid.UUID | None = None
    software_version: str = "0.1.0"


class ExperimentResultItem(BaseModel):
    """Normalized experiment result entry with complete provenance and raw result payload."""

    analysis_id: uuid.UUID
    analysis_type: str
    created_at: datetime
    software_version: str
    dataset: DatasetProvenanceSummary
    experiment: ExperimentProvenanceSummary
    comparison: ComparisonProvenanceSummary | None = None
    provenance: ResultProvenance
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ExperimentResultsResponse(BaseModel):
    """Structured response containing all analysis results and provenance for an experiment."""

    experiment_id: uuid.UUID
    experiment_name: str
    total_results: int
    results: list[ExperimentResultItem]
