from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.scientific.statistics.models import (
    AnalysisCategory,
    AssumptionResult,
    ConfidenceIntervalResult,
    EffectSizeResult,
    PostHocMethod,
    PostHocResult,
    StatisticalMethod,
)


class StatisticalAnalysisRequestSchema(BaseModel):
    """API request model for executing a statistical hypothesis test."""

    category: AnalysisCategory
    method: StatisticalMethod
    value_column: str = Field(..., description="Target numeric measurement column")
    group_column: str | None = Field(None, description="Categorical grouping column (if applicable)")
    value_column_2: str | None = Field(
        None, description="Second numeric measurement column for correlation or paired tests"
    )
    alpha: float = Field(default=0.05, ge=0.001, le=0.20, description="Significance threshold alpha")
    post_hoc_method: PostHocMethod = Field(default=PostHocMethod.NONE, description="Multiple comparison adjustment")
    paired: bool = Field(default=False, description="Whether observations are paired/dependent")


class StatisticalAnalysisResponseSchema(BaseModel):
    """API response model for statistical hypothesis test results."""

    dataset_id: UUID | None = None
    test_name: str
    category: AnalysisCategory
    method: StatisticalMethod
    variables: dict[str, Any]
    statistic_name: str
    statistic_value: float | None = None
    p_value: float | None = None
    df: Any | None = None
    alpha: float = 0.05
    is_significant: bool = False
    sample_size: dict[str, int] | int
    effect_size: EffectSizeResult | None = None
    confidence_interval: ConfidenceIntervalResult | None = None
    assumptions: list[AssumptionResult] = Field(default_factory=list)
    post_hoc: list[PostHocResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    statement: str
