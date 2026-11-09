import numpy as np
import pandas as pd
from scipy import stats

from app.scientific.statistics.models import AssumptionResult


def check_normality(series: pd.Series, variable_label: str = "variable", alpha: float = 0.05) -> AssumptionResult:
    """Evaluates normality assumption using Shapiro-Wilk (N <= 5000) or D'Agostino-Pearson (N > 5000)."""
    clean_series = pd.to_numeric(series, errors="coerce").dropna()
    n = len(clean_series)

    if n < 3:
        return AssumptionResult(
            name=f"Normality ({variable_label})",
            statistic=None,
            p_value=None,
            passed=False,
            details=f"Insufficient sample size (N={n}, minimum 3 required for normality test).",
        )

    # Check for constant series (variance = 0)
    if clean_series.nunique() == 1 or clean_series.std() == 0:
        return AssumptionResult(
            name=f"Normality ({variable_label})",
            statistic=None,
            p_value=None,
            passed=False,
            details="Constant values detected (zero variance). Normality test is not applicable.",
        )

    try:
        if n <= 5000:
            stat, p_val = stats.shapiro(clean_series)
            test_name = "Shapiro-Wilk"
        else:
            stat, p_val = stats.normaltest(clean_series)
            test_name = "D'Agostino-Pearson"

        # Sanitize float outputs
        stat_val = float(stat) if not np.isnan(stat) else None
        p_val_float = float(p_val) if not np.isnan(p_val) else None
        passed = (p_val_float >= alpha) if p_val_float is not None else False

        norm_desc = (
            "No significant departure from normality detected"
            if passed
            else "Significant departure from normality detected"
        )
        detail = f"{test_name} test: stat={stat_val:.4f}, p={p_val_float:.4f}. {norm_desc} (alpha={alpha})."
        return AssumptionResult(
            name=f"Normality ({variable_label})",
            statistic=stat_val,
            p_value=p_val_float,
            passed=passed,
            details=detail,
        )
    except Exception as exc:
        return AssumptionResult(
            name=f"Normality ({variable_label})",
            statistic=None,
            p_value=None,
            passed=False,
            details=f"Normality check could not be computed: {str(exc)}",
        )


def check_homogeneity(groups_data: list[pd.Series], group_labels: list[str], alpha: float = 0.05) -> AssumptionResult:
    """Evaluates homogeneity of variance assumption across groups using Levene's test."""
    clean_groups = []
    for g in groups_data:
        cg = pd.to_numeric(g, errors="coerce").dropna()
        if len(cg) >= 2:
            clean_groups.append(cg)

    if len(clean_groups) < 2:
        return AssumptionResult(
            name="Homogeneity of Variance (Levene)",
            statistic=None,
            p_value=None,
            passed=False,
            details="Fewer than 2 valid groups with N>=2. Levene's test cannot be evaluated.",
        )

    try:
        stat, p_val = stats.levene(*clean_groups)
        stat_val = float(stat) if not np.isnan(stat) else None
        p_val_float = float(p_val) if not np.isnan(p_val) else None
        passed = (p_val_float >= alpha) if p_val_float is not None else False

        homo_desc = (
            "No significant difference in group variances detected"
            if passed
            else "Significant difference in group variances detected (heteroscedasticity)"
        )
        detail = f"Levene's test: stat={stat_val:.4f}, p={p_val_float:.4f}. {homo_desc} (alpha={alpha})."
        return AssumptionResult(
            name="Homogeneity of Variance (Levene)",
            statistic=stat_val,
            p_value=p_val_float,
            passed=passed,
            details=detail,
        )
    except Exception as exc:
        return AssumptionResult(
            name="Homogeneity of Variance (Levene)",
            statistic=None,
            p_value=None,
            passed=False,
            details=f"Homogeneity check could not be computed: {str(exc)}",
        )
