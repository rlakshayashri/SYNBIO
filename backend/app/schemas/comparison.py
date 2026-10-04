import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.statistical_analysis import StatisticalAnalysisResponseSchema
from app.schemas.statistics import DescriptiveStatisticsResult
from app.scientific.statistics.models import (
    AnalysisCategory,
    PostHocMethod,
    StatisticalMethod,
)


class GroupDataSummary(BaseModel):
    """Summary of observation data and descriptive statistics for an experimental group."""

    group_id: uuid.UUID | None = Field(default=None, description="ID of ExperimentalGroup model if linked.")
    group_name: str = Field(..., description="Name or identifier of group.")
    group_code: str | None = Field(default=None, description="Group code matching data values.")
    is_control: bool = Field(default=False, description="Flag indicating control group status.")
    sample_size_total: int = Field(..., description="Total row count for group.")
    sample_size_valid: int = Field(..., description="Valid numeric count for group.")
    missing_count: int = Field(..., description="Missing/NaN/null count for group.")
    descriptive_stats: DescriptiveStatisticsResult | None = Field(
        default=None, description="Descriptive statistics computed for group observations."
    )


class ComparisonCreateRequest(BaseModel):
    """Schema for requesting a new experimental group comparison."""

    name: str = Field(..., min_length=1, max_length=255, description="Name/title of comparison.")
    comparison_type: str = Field(
        default="two_group",
        description="Type of comparison ('two_group', 'anova', 'nonparametric')",
    )
    group_a_id: uuid.UUID | None = Field(default=None, description="Primary experimental group ID (or control).")
    group_b_id: uuid.UUID | None = Field(default=None, description="Secondary experimental group ID (or treatment).")
    measurement_column: str = Field(..., min_length=1, description="Numeric measurement column name in dataset.")
    group_column: str | None = Field(
        default=None, description="Categorical column in dataset representing group codes."
    )
    category: AnalysisCategory = Field(default=AnalysisCategory.TWO_GROUP, description="Statistical analysis category.")
    method: StatisticalMethod = Field(
        default=StatisticalMethod.WELCH_TTEST, description="Statistical hypothesis test method."
    )
    alpha: float = Field(default=0.05, ge=0.001, le=0.20, description="Significance threshold alpha.")
    post_hoc_method: PostHocMethod = Field(
        default=PostHocMethod.NONE, description="Post-hoc multiple comparison adjustment."
    )
    paired: bool = Field(default=False, description="Flag for paired/matched-pairs statistical test.")


class ComparisonResponse(BaseModel):
    """Schema for Comparison response."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    analysis_id: uuid.UUID | None = None
    name: str
    comparison_type: str
    group_a_id: uuid.UUID | None = None
    group_b_id: uuid.UUID | None = None
    measurement_column: str
    group_column: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    result_summary: dict[str, Any] = Field(default_factory=dict)
    statistical_result: StatisticalAnalysisResponseSchema | None = None
    group_summaries: list[GroupDataSummary] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
