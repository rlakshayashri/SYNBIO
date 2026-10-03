import numpy as np
import pandas as pd
from scipy import stats

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.assumptions import check_normality
from app.scientific.statistics.confidence_intervals import calculate_pearson_r_ci
from app.scientific.statistics.effect_sizes import interpret_correlation_effect_size
from app.scientific.statistics.models import (
    AnalysisCategory,
    StatisticalAnalysisResult,
    StatisticalMethod,
)


def run_correlation_analysis(
    df: pd.DataFrame,
    column_1: str,
    column_2: str,
    method: StatisticalMethod = StatisticalMethod.PEARSON,
    alpha: float = 0.05,
) -> StatisticalAnalysisResult:
    """Executes Pearson or Spearman correlation analysis between two numeric variables."""
    if column_1 not in df.columns:
        raise ScientificValidationError(f"Column '{column_1}' not found in dataset.")
    if column_2 not in df.columns:
        raise ScientificValidationError(f"Column '{column_2}' not found in dataset.")

    # Subset & pairwise drop missing
    clean_df = df[[column_1, column_2]].copy()
    clean_df[column_1] = pd.to_numeric(clean_df[column_1], errors="coerce")
    clean_df[column_2] = pd.to_numeric(clean_df[column_2], errors="coerce")
    clean_df = clean_df.dropna()

    n_total = len(df)
    n_analyzed = len(clean_df)
    n_missing = n_total - n_analyzed

    warnings = []
    if n_missing > 0:
        warnings.append(f"{n_missing} observation(s) dropped due to missing values in target columns.")

    if n_analyzed < 3:
        raise ScientificValidationError(
            f"Insufficient observations (N={n_analyzed}). Minimum 3 complete pairs required for correlation."
        )

    s1, s2 = clean_df[column_1], clean_df[column_2]

    if s1.nunique() == 1 or s2.nunique() == 1:
        raise ScientificValidationError(
            "One or both target columns have constant values (zero variance). Correlation cannot be computed."
        )

    # Assumption checks
    norm_1 = check_normality(s1, variable_label=column_1, alpha=alpha)
    norm_2 = check_normality(s2, variable_label=column_2, alpha=alpha)
    assumptions = [norm_1, norm_2]

    if method == StatisticalMethod.PEARSON:
        stat, p_val = stats.pearsonr(s1, s2)
        stat_name = "Pearson r"
        test_title = "Pearson Correlation Analysis"
        ci = calculate_pearson_r_ci(float(stat), n_analyzed, alpha=alpha)
        if not (norm_1.passed and norm_2.passed):
            warnings.append(
                "Normality assumption violated for one or both variables. Consider Spearman rank correlation."
            )
    else:
        stat, p_val = stats.spearmanr(s1, s2)
        stat_name = "Spearman rho"
        test_title = "Spearman Rank Correlation Analysis"
        ci = None

    stat_val = float(stat) if not np.isnan(stat) else None
    p_val_float = float(p_val) if not np.isnan(p_val) else None
    is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

    effect_size = interpret_correlation_effect_size(stat_val or 0.0, name=stat_name)

    df_val = n_analyzed - 2

    # Factual statement construction
    ci_str = f", 95% CI: [{ci.lower:.4f}, {ci.upper:.4f}]" if ci and ci.lower is not None else ""
    statement = (
        f"{test_title} between '{column_1}' and '{column_2}' returned "
        f"{stat_name} = {stat_val:.4f}, p = {p_val_float:.4f} at α = {alpha} "
        f"(N = {n_analyzed}{ci_str}, Effect Size: {effect_size.interpretation})."
    )

    return StatisticalAnalysisResult(
        test_name=test_title,
        category=AnalysisCategory.CORRELATION,
        method=method,
        variables={
            "column_1": column_1,
            "column_2": column_2,
            "n_total": n_total,
            "n_analyzed": n_analyzed,
            "n_missing": n_missing,
        },
        statistic_name=stat_name,
        statistic_value=round(stat_val, 4) if stat_val is not None else None,
        p_value=round(p_val_float, 4) if p_val_float is not None else None,
        df=df_val,
        alpha=alpha,
        is_significant=is_sig,
        sample_size={"n_total": n_total, "n_analyzed": n_analyzed},
        effect_size=effect_size,
        confidence_interval=ci,
        assumptions=assumptions,
        warnings=warnings,
        statement=statement,
    )
