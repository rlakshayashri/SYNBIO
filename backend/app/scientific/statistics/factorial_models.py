from pydantic import BaseModel, Field

from app.scientific.statistics.models import AssumptionResult, PostHocMethod, PostHocResult


class AnovaEffectResult(BaseModel):
    """Statistical summary for a single ANOVA effect (main effect, interaction, or residual)."""

    effect_name: str
    df: float
    sum_sq: float
    mean_sq: float | None = None
    f_statistic: float | None = None
    p_value: float | None = None
    is_significant: bool = False
    partial_eta_squared: float | None = None
    partial_eta_squared_ci: list[float] | None = None
    effect_size_interpretation: str | None = None


class SimpleEffectResult(BaseModel):
    """Simple main effect test of one factor evaluated at a specific slice level of another factor."""

    slice_factor: str
    slice_level: str
    target_factor: str
    df_between: float | None = None
    df_within: float | None = None
    f_statistic: float | None = None
    p_value: float | None = None
    is_significant: bool = False
    pairwise_comparisons: list[PostHocResult] = Field(default_factory=list)


class FactorialAnalysisOptions(BaseModel):
    """Configuration options for Two-Way ANOVA execution."""

    alpha: float = Field(default=0.05, ge=0.001, le=0.20, description="Significance threshold alpha.")
    post_hoc_method: PostHocMethod = Field(
        default=PostHocMethod.TUKEY, description="Multiple comparison post-hoc adjustment."
    )
    perform_simple_effects: bool = Field(
        default=True, description="Whether to compute simple main effects when interaction is significant."
    )
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.999, description="Confidence level for intervals.")


class TwoWayAnovaResult(BaseModel):
    """Framework-independent structured result of two-factor factorial ANOVA."""

    test_name: str = "Two-Way ANOVA (Type III SS)"
    model_formula: str
    response_column: str
    factor_a_column: str
    factor_b_column: str
    factor_a_levels: list[str]
    factor_b_levels: list[str]
    cell_sample_sizes: dict[str, int]
    total_rows_input: int
    valid_rows_used: int
    excluded_rows_count: int
    exclusion_reasons: dict[str, int]
    design_balance: str
    is_balanced: bool
    contrast_coding: str = "sum-to-zero (deviation)"
    anova_type: str = "Type III"
    effects: dict[str, AnovaEffectResult]
    assumptions: list[AssumptionResult]
    interaction_significant: bool
    post_hoc_method: str
    post_hoc_comparisons: list[PostHocResult] = Field(default_factory=list)
    simple_effects: list[SimpleEffectResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    scientific_statement: str
