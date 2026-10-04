from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExperimentReportHeader(BaseModel):
    """Experiment Report Metadata Header DTO."""

    experiment_id: UUID
    experiment_name: str
    description: str | None = None
    objective: str | None = None
    status: str
    organism: str | None = None
    condition_type: str | None = None
    assay_type: str | None = None
    target_gene: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    report_generated_at: datetime
    software_version: str = "0.1.0"


class GroupReplicateReportItem(BaseModel):
    """Replicate Item DTO for Report Experimental Context."""

    id: UUID
    replicate_name: str
    sample_identifier: str | None = None
    row_index: int | None = None
    replicate_type: str = "biological"
    metadata_payload: dict[str, Any] = Field(default_factory=dict)


class ExperimentalGroupReportItem(BaseModel):
    """Experimental Group Item DTO for Report Experimental Context."""

    id: UUID
    name: str
    group_code: str
    is_control: bool = False
    description: str | None = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    replicates: list[GroupReplicateReportItem] = Field(default_factory=list)


class ExperimentalContextReport(BaseModel):
    """Experimental Context DTO summarizing recorded experimental parameters and groups."""

    experiment_name: str
    description: str | None = None
    objective: str | None = None
    status: str
    organism: str | None = None
    condition_type: str | None = None
    assay_type: str | None = None
    target_gene: str | None = None
    notes: str | None = None
    groups: list[ExperimentalGroupReportItem] = Field(default_factory=list)


class DatasetReportItem(BaseModel):
    """Attached Dataset Summary Item DTO for Scientific Report."""

    dataset_id: UUID
    dataset_name: str
    file_name: str
    file_type: str
    file_size: int
    row_count: int | None = None
    column_count: int | None = None
    created_at: datetime
    has_validation: bool = False


class DataQualityReportItem(BaseModel):
    """Data Quality / Validation Result DTO for Scientific Report."""

    analysis_id: UUID
    dataset_id: UUID
    dataset_name: str
    created_at: datetime
    missing_values: dict[str, Any] | None = None
    duplicate_rows: int | None = None
    detected_data_types: dict[str, Any] | None = None
    empty_columns: list[str] | None = None
    outliers_summary: dict[str, Any] | None = None
    validation_passed: bool | None = None


class DescriptiveStatisticsReportItem(BaseModel):
    """Numeric Column Descriptive Statistics Result DTO for Scientific Report."""

    analysis_id: UUID
    dataset_id: UUID
    dataset_name: str
    created_at: datetime
    column_name: str
    count: int | None = None
    missing_count: int | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    variance: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    range_val: float | None = None
    q1: float | None = None
    q2: float | None = None
    q3: float | None = None
    iqr: float | None = None
    cv: float | None = None


class VisualizationReportItem(BaseModel):
    """Scientific Visualization Configuration / Output Metadata DTO."""

    analysis_id: UUID
    dataset_id: UUID
    dataset_name: str
    created_at: datetime
    visualization_type: str
    configuration: dict[str, Any] = Field(default_factory=dict)


class ComparisonReportItem(BaseModel):
    """Experimental Group Comparison Record DTO for Scientific Report."""

    comparison_id: UUID
    comparison_name: str
    comparison_type: str
    dataset_id: UUID | None = None
    dataset_name: str | None = None
    group_a_name: str | None = None
    group_b_name: str | None = None
    group_column: str | None = None
    measurement_column: str
    statistical_method: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class StatisticalResultReportItem(BaseModel):
    """Statistical Analysis Test Result DTO for Scientific Report."""

    analysis_id: UUID
    analysis_type: str
    dataset_id: UUID
    dataset_name: str
    comparison_id: UUID | None = None
    created_at: datetime
    test_name: str | None = None
    statistic_name: str | None = None
    statistic_value: float | None = None
    p_value: float | None = None
    degrees_of_freedom: float | None = None
    effect_size_name: str | None = None
    effect_size_value: float | None = None
    confidence_interval: list[float] | None = None
    is_significant: bool | None = None
    assumption_checks: dict[str, Any] | None = None
    raw_result: dict[str, Any] = Field(default_factory=dict)


class ProvenanceReportItem(BaseModel):
    """Traceability & Provenance Entry DTO for Report Section Evidence."""

    section: str
    analysis_id: UUID | None = None
    analysis_type: str | None = None
    comparison_id: UUID | None = None
    dataset_id: UUID | None = None
    dataset_name: str | None = None
    experiment_id: UUID
    software_version: str = "0.1.0"
    created_at: datetime


class ExperimentReport(BaseModel):
    """Complete Deterministic Scientific Experiment Report DTO."""

    metadata: ExperimentReportHeader
    experimental_context: ExperimentalContextReport
    datasets: list[DatasetReportItem] = Field(default_factory=list)
    data_quality: list[DataQualityReportItem] = Field(default_factory=list)
    descriptive_statistics: list[DescriptiveStatisticsReportItem] = Field(default_factory=list)
    visualizations: list[VisualizationReportItem] = Field(default_factory=list)
    comparisons: list[ComparisonReportItem] = Field(default_factory=list)
    statistical_results: list[StatisticalResultReportItem] = Field(default_factory=list)
    provenance: list[ProvenanceReportItem] = Field(default_factory=list)
    generated_at: datetime
    disclaimer: str = (
        "SynDataX reports recorded experimental evidence and statistical results. "
        "It does not automatically establish biological causality or biological significance."
    )
