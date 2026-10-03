from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ColumnStatistics(BaseModel):
    """Descriptive statistics for a single numeric column."""

    column: str
    count: int
    missing_count: int
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    variance: float | None = None
    min: float | None = None
    max: float | None = None
    q1: float | None = None
    q2: float | None = None
    q3: float | None = None
    iqr: float | None = None
    range: float | None = None
    cv: float | None = None


class DescriptiveStatisticsResult(BaseModel):
    """Structured result produced by the scientific statistics engine."""

    dataset_id: UUID | None = None
    row_count: int
    numeric_column_count: int
    non_numeric_column_count: int
    statistics: list[ColumnStatistics]
    skipped_columns: list[str] = Field(default_factory=list)


# --- Module 5 Statistical Analysis Models ---


class AnalysisCategory(StrEnum):
    TWO_GROUP = "two_group"
    ANOVA = "anova"
    NONPARAMETRIC = "nonparametric"
    CORRELATION = "correlation"


class StatisticalMethod(StrEnum):
    # Two-group parametric
    STUDENT_TTEST = "student_ttest"
    WELCH_TTEST = "welch_ttest"
    PAIRED_TTEST = "paired_ttest"

    # Multi-group ANOVA
    ONE_WAY_ANOVA = "one_way_anova"
    WELCH_ANOVA = "welch_anova"

    # Non-parametric
    MANN_WHITNEY = "mann_whitney"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    KRUSKAL_WALLIS = "kruskal_wallis"

    # Correlation
    PEARSON = "pearson"
    SPEARMAN = "spearman"


class PostHocMethod(StrEnum):
    NONE = "none"
    TUKEY = "tukey"
    BONFERRONI = "bonferroni"
    HOLM = "holm"


class StatisticalAnalysisRequest(BaseModel):
    """Request model for running a statistical hypothesis test."""

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


class AssumptionResult(BaseModel):
    """Result of a statistical assumption check (normality, equal variance, etc.)."""

    name: str
    statistic: float | None = None
    p_value: float | None = None
    passed: bool
    details: str


class EffectSizeResult(BaseModel):
    """Quantified effect size metric."""

    name: str
    value: float | None = None
    interpretation: str | None = None  # e.g., "negligible", "small", "medium", "large"


class ConfidenceIntervalResult(BaseModel):
    """Confidence interval bounds for an estimated metric."""

    level: float = 0.95
    lower: float | None = None
    upper: float | None = None
    metric: str = "difference"


class PostHocResult(BaseModel):
    """Pairwise post-hoc comparison result."""

    group1: str
    group2: str
    statistic: float | None = None
    p_raw: float | None = None
    p_adjusted: float | None = None
    correction_method: str = "none"
    is_significant: bool = False


class StatisticalAnalysisResult(BaseModel):
    """Complete, transparent statistical analysis output."""

    dataset_id: UUID | None = None
    test_name: str
    category: AnalysisCategory
    method: StatisticalMethod
    variables: dict[str, Any]
    statistic_name: str
    statistic_value: float | None = None
    p_value: float | None = None
    df: Any | None = None  # float, int, or dict for multi-df like ANOVA (df_between, df_within)
    alpha: float = 0.05
    is_significant: bool = False
    sample_size: dict[str, int] | int
    effect_size: EffectSizeResult | None = None
    confidence_interval: ConfidenceIntervalResult | None = None
    assumptions: list[AssumptionResult] = Field(default_factory=list)
    post_hoc: list[PostHocResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    statement: str
