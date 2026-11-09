"""Scientific statistics subpackage (descriptive stats, hypothesis tests, correlation, ANOVA, non-parametric)."""

from app.scientific.statistics.anova import run_anova_analysis
from app.scientific.statistics.correlation import run_correlation_analysis
from app.scientific.statistics.descriptive import calculate_descriptive_statistics
from app.scientific.statistics.factorial_models import (
    AnovaEffectResult,
    FactorialAnalysisOptions,
    SimpleEffectResult,
    TwoWayAnovaResult,
)
from app.scientific.statistics.group_comparison import run_two_group_comparison
from app.scientific.statistics.models import (
    AnalysisCategory,
    AssumptionResult,
    ColumnStatistics,
    ConfidenceIntervalResult,
    DescriptiveStatisticsResult,
    EffectSizeResult,
    PostHocMethod,
    PostHocResult,
    StatisticalAnalysisRequest,
    StatisticalAnalysisResult,
    StatisticalMethod,
)
from app.scientific.statistics.nonparametric import run_nonparametric_group_comparison
from app.scientific.statistics.two_way_anova import (
    calculate_partial_eta_squared,
    compute_simple_effects,
    compute_two_way_anova,
    validate_factorial_inputs,
)

__all__ = [
    "calculate_descriptive_statistics",
    "run_correlation_analysis",
    "run_two_group_comparison",
    "run_anova_analysis",
    "run_nonparametric_group_comparison",
    "ColumnStatistics",
    "DescriptiveStatisticsResult",
    "AnalysisCategory",
    "StatisticalMethod",
    "PostHocMethod",
    "StatisticalAnalysisRequest",
    "AssumptionResult",
    "EffectSizeResult",
    "ConfidenceIntervalResult",
    "PostHocResult",
    "StatisticalAnalysisResult",
    "compute_two_way_anova",
    "validate_factorial_inputs",
    "calculate_partial_eta_squared",
    "compute_simple_effects",
    "AnovaEffectResult",
    "SimpleEffectResult",
    "FactorialAnalysisOptions",
    "TwoWayAnovaResult",
]
