import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.scientific.statistics.factorial_models import TwoWayAnovaResult
from app.scientific.statistics.models import PostHocMethod


class FactorialComparisonBase(BaseModel):
    """Base schema for FactorialComparison configuration."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the factorial comparison.")
    description: str | None = Field(default=None, description="Optional description.")
    dataset_id: uuid.UUID | None = Field(default=None, description="Optional ID of dataset analyzed.")
    factor_a_id: uuid.UUID | None = Field(default=None, description="Optional ID of first registered factor.")
    factor_b_id: uuid.UUID | None = Field(default=None, description="Optional ID of second registered factor.")
    factor_a_column: str = Field(..., min_length=1, max_length=255, description="Dataset column for Factor A.")
    factor_b_column: str = Field(..., min_length=1, max_length=255, description="Dataset column for Factor B.")
    measurement_column: str = Field(
        ..., min_length=1, max_length=255, description="Dataset column for measurement/response variable."
    )
    parameters: dict[str, Any] = Field(default_factory=dict, description="Factorial analysis parameters.")


class FactorialComparisonCreate(FactorialComparisonBase):
    """Schema for creating and executing a FactorialComparison record."""

    alpha: float = Field(default=0.05, ge=0.001, le=0.20, description="Significance threshold alpha.")
    post_hoc_method: PostHocMethod = Field(
        default=PostHocMethod.TUKEY, description="Post-hoc multiple comparison adjustment."
    )
    check_assumptions: bool = Field(default=True, description="Whether to check ANOVA assumptions.")


class FactorialComparisonUpdate(BaseModel):
    """Schema for updating a FactorialComparison record."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    status: str | None = Field(default=None, max_length=50)
    parameters: dict[str, Any] | None = Field(default=None)
    result_summary: dict[str, Any] | None = Field(default=None)


class FactorialComparisonResponse(FactorialComparisonBase):
    """Schema for returning FactorialComparison details."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    analysis_id: uuid.UUID | None = None
    status: str
    result_summary: dict[str, Any] = Field(default_factory=dict)
    two_way_anova_result: TwoWayAnovaResult | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_two_way_anova_result(self) -> "FactorialComparisonResponse":
        """Attempts to parse typed TwoWayAnovaResult from result_summary if not already present."""
        if self.two_way_anova_result is None and self.result_summary and "effects" in self.result_summary:
            try:
                self.two_way_anova_result = TwoWayAnovaResult.model_validate(self.result_summary)
            except Exception:
                pass
        return self

