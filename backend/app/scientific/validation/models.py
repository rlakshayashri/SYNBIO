from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationStatus(StrEnum):
    """Overall data quality validation status."""

    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MissingValueCheck(BaseModel):
    """Missing value details per column."""

    column: str
    missing_count: int
    missing_percentage: float


class DuplicateCheck(BaseModel):
    """Exact duplicate row details."""

    duplicate_count: int
    duplicate_percentage: float


class DataTypeCheck(BaseModel):
    """Detected pandas data type per column."""

    column: str
    detected_dtype: str


class OutlierCheck(BaseModel):
    """IQR outlier details for numeric columns."""

    column: str
    outlier_count: int
    outlier_percentage: float
    lower_bound: float
    upper_bound: float


class ValidationSummary(BaseModel):
    """Aggregated count summary of data quality findings."""

    missing_values: int
    duplicate_rows: int
    potential_outliers: int
    empty_columns: int


class ValidationChecks(BaseModel):
    """Detailed validation check results."""

    missing_values: list[MissingValueCheck]
    duplicates: DuplicateCheck
    data_types: list[DataTypeCheck]
    outliers: list[OutlierCheck]
    empty_columns: list[str]


class ValidationResult(BaseModel):
    """Structured result produced by the scientific validation engine."""

    dataset_id: UUID | None = None
    row_count: int
    column_count: int
    overall_status: ValidationStatus
    summary: ValidationSummary
    checks: ValidationChecks
    warnings: list[str] = Field(default_factory=list)
