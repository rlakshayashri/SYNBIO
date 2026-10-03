import numpy as np
import pandas as pd
from scipy import stats

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.assumptions import check_homogeneity, check_normality
from app.scientific.statistics.effect_sizes import calculate_eta_squared
from app.scientific.statistics.models import (
    AnalysisCategory,
    PostHocMethod,
    StatisticalAnalysisResult,
    StatisticalMethod,
)
from app.scientific.statistics.multiple_comparison import (
    run_post_hoc_pairwise_ttest,
    run_post_hoc_tukey,
)


def run_anova_analysis(
    df: pd.DataFrame,
    value_column: str,
    group_column: str,
    method: StatisticalMethod = StatisticalMethod.ONE_WAY_ANOVA,
    alpha: float = 0.05,
    post_hoc_method: PostHocMethod = PostHocMethod.TUKEY,
) -> StatisticalAnalysisResult:
    """Executes One-Way ANOVA or Welch's ANOVA across multiple categorical groups."""
    if group_column not in df.columns:
        raise ScientificValidationError(f"Group column '{group_column}' not found in dataset.")
    if value_column not in df.columns:
        raise ScientificValidationError(f"Value column '{value_column}' not found in dataset.")

    clean_df = df[[value_column, group_column]].dropna().copy()
    clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
    clean_df = clean_df.dropna()

    groups = sorted(clean_df[group_column].unique())
    if len(groups) < 2:
        raise ScientificValidationError(
            f"ANOVA requires at least 2 unique groups in '{group_column}'. Found {len(groups)}."
        )

    group_series_list = [clean_df[clean_df[group_column] == g][value_column] for g in groups]
    sample_sizes = {str(g): len(s) for g, s in zip(groups, group_series_list, strict=False)}

    for g_label, n in sample_sizes.items():
        if n < 2:
            raise ScientificValidationError(
                f"Group '{g_label}' has insufficient sample size (N={n}). Minimum 2 observations per group required."
            )

    warnings = []

    # Assumptions
    assumptions = []
    for g_label, s in zip(groups, group_series_list, strict=False):
        norm_res = check_normality(s, variable_label=str(g_label), alpha=alpha)
        assumptions.append(norm_res)
        if not norm_res.passed:
            warnings.append(f"Normality assumption violated for group '{g_label}' (p < alpha).")

    homo = check_homogeneity(group_series_list, [str(g) for g in groups], alpha=alpha)
    assumptions.append(homo)

    if method == StatisticalMethod.WELCH_ANOVA:
        # Welch's ANOVA using stats.f_oneway with unequal variances or scipy.stats.alexandergovern / statsmodels
        # SciPy 1.7+ has stats.alexandergovern or Welch ANOVA via statsmodels.
        # Alternatively compute Welch ANOVA via scipy stats or custom formula
        # Let's compute Welch F statistic:
        k = len(groups)
        ni = np.array([len(s) for s in group_series_list])
        vi = np.array([s.var(ddof=1) for s in group_series_list])
        wi = ni / vi
        w_sum = np.sum(wi)
        xbar_i = np.array([s.mean() for s in group_series_list])
        xbar_w = np.sum(wi * xbar_i) / w_sum

        f_num = np.sum(wi * (xbar_i - xbar_w) ** 2) / (k - 1)
        tmp = np.sum((1.0 - wi / w_sum) ** 2 / (ni - 1))
        f_den = 1.0 + (2.0 * (k - 2) / (k**2 - 1)) * tmp
        f_stat = f_num / f_den

        df1 = k - 1
        df2 = (k**2 - 1) / (3.0 * tmp)
        p_val = 1.0 - stats.f.cdf(f_stat, df1, df2)

        stat_name = "Welch F"
        test_title = "Welch's One-Way ANOVA"
        df_val = {"df_between": round(float(df1), 2), "df_within": round(float(df2), 2)}
    else:
        # Standard One-Way ANOVA
        f_stat, p_val = stats.f_oneway(*group_series_list)
        stat_name = "F"
        test_title = "One-Way ANOVA"

        k = len(groups)
        total_n = sum(sample_sizes.values())
        df_between = k - 1
        df_within = total_n - k
        df_val = {"df_between": df_between, "df_within": df_within}

        if not homo.passed:
            warnings.append(
                "Homogeneity of variance assumption violated (Levene p < alpha). Welch's ANOVA is recommended."
            )

    f_stat_val = float(f_stat) if not np.isnan(f_stat) else None
    p_val_float = float(p_val) if not np.isnan(p_val) else None
    is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

    effect_size = calculate_eta_squared(group_series_list)

    # Post-Hoc Multiple Comparisons
    post_hoc_results = []
    if post_hoc_method != PostHocMethod.NONE:
        if post_hoc_method == PostHocMethod.TUKEY:
            post_hoc_results = run_post_hoc_tukey(clean_df, value_column, group_column, alpha=alpha)
        elif post_hoc_method in [PostHocMethod.BONFERRONI, PostHocMethod.HOLM]:
            post_hoc_results = run_post_hoc_pairwise_ttest(
                clean_df,
                value_column,
                group_column,
                method=post_hoc_method,
                alpha=alpha,
            )

    statement = (
        f"{test_title} across {len(groups)} groups ('{group_column}') for measurement '{value_column}' "
        f"returned {stat_name} = {f_stat_val:.4f}, p = {p_val_float:.4f} at α = {alpha} "
        f"(Effect Size: {effect_size.interpretation}, eta^2 = {effect_size.value})."
    )

    return StatisticalAnalysisResult(
        test_name=test_title,
        category=AnalysisCategory.ANOVA,
        method=method,
        variables={
            "value_column": value_column,
            "group_column": group_column,
            "groups": [str(g) for g in groups],
            "num_groups": len(groups),
        },
        statistic_name=stat_name,
        statistic_value=round(f_stat_val, 4) if f_stat_val is not None else None,
        p_value=round(p_val_float, 4) if p_val_float is not None else None,
        df=df_val,
        alpha=alpha,
        is_significant=is_sig,
        sample_size=sample_sizes,
        effect_size=effect_size,
        confidence_interval=None,
        assumptions=assumptions,
        post_hoc=post_hoc_results,
        warnings=warnings,
        statement=statement,
    )
