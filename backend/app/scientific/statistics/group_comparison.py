import numpy as np
import pandas as pd
from scipy import stats

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.assumptions import check_homogeneity, check_normality
from app.scientific.statistics.confidence_intervals import calculate_mean_diff_ci
from app.scientific.statistics.effect_sizes import calculate_cohens_d
from app.scientific.statistics.models import (
    AnalysisCategory,
    StatisticalAnalysisResult,
    StatisticalMethod,
)


def run_two_group_comparison(
    df: pd.DataFrame,
    value_column: str,
    group_column: str | None = None,
    value_column_2: str | None = None,
    method: StatisticalMethod = StatisticalMethod.WELCH_TTEST,
    alpha: float = 0.05,
    paired: bool = False,
) -> StatisticalAnalysisResult:
    """Executes parametric two-group comparisons (Student's, Welch's, or Paired t-test)."""
    warnings = []

    # Extract group series based on input configuration
    if group_column:
        if group_column not in df.columns:
            raise ScientificValidationError(f"Group column '{group_column}' not found.")
        if value_column not in df.columns:
            raise ScientificValidationError(f"Value column '{value_column}' not found.")

        clean_df = df[[value_column, group_column]].dropna().copy()
        clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
        clean_df = clean_df.dropna()

        unique_groups = list(clean_df[group_column].unique())
        if len(unique_groups) != 2:
            raise ScientificValidationError(
                f"Group column '{group_column}' must contain exactly 2 unique groups. Found {len(unique_groups)}."
            )

        g1_label, g2_label = str(unique_groups[0]), str(unique_groups[1])
        s1 = clean_df[clean_df[group_column] == unique_groups[0]][value_column]
        s2 = clean_df[clean_df[group_column] == unique_groups[1]][value_column]
    elif value_column_2:
        if value_column not in df.columns:
            raise ScientificValidationError(f"Value column '{value_column}' not found.")
        if value_column_2 not in df.columns:
            raise ScientificValidationError(f"Value column '{value_column_2}' not found.")

        clean_df = df[[value_column, value_column_2]].dropna().copy()
        clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
        clean_df[value_column_2] = pd.to_numeric(clean_df[value_column_2], errors="coerce")
        clean_df = clean_df.dropna()

        g1_label, g2_label = value_column, value_column_2
        s1 = clean_df[value_column]
        s2 = clean_df[value_column_2]
    else:
        raise ScientificValidationError(
            "Either a group_column or value_column_2 must be specified for two-group comparison."
        )

    n1, n2 = len(s1), len(s2)
    if n1 < 2 or n2 < 2:
        raise ScientificValidationError(
            f"Insufficient sample size (Group 1 N={n1}, Group 2 N={n2}). Minimum 2 observations per group required."
        )

    if paired and n1 != n2:
        raise ScientificValidationError(f"Paired t-test requires equal sample sizes (Group 1 N={n1}, Group 2 N={n2}).")

    if n1 < 15 or n2 < 15:
        warnings.append(f"Small sample size detected (N1={n1}, N2={n2}). Normality test power may be limited.")

    # Assumption checks
    norm_1 = check_normality(s1, variable_label=g1_label, alpha=alpha)
    norm_2 = check_normality(s2, variable_label=g2_label, alpha=alpha)
    homo = check_homogeneity([s1, s2], [g1_label, g2_label], alpha=alpha)
    assumptions = [norm_1, norm_2, homo]

    if not (norm_1.passed and norm_2.passed):
        warnings.append("Normality assumption violated for one or both groups. Consider Mann-Whitney U test.")

    # Execute test method
    if method == StatisticalMethod.PAIRED_TTEST or paired:
        stat, p_val = stats.ttest_rel(s1, s2)
        stat_name = "Paired t"
        test_title = "Paired Two-Sample t-test"
        df_val = n1 - 1
        effect_size = calculate_cohens_d(s1, s2, paired=True)
        ci = calculate_mean_diff_ci(s1, s2, alpha=alpha, paired=True)
    elif method == StatisticalMethod.STUDENT_TTEST:
        stat, p_val = stats.ttest_ind(s1, s2, equal_var=True)
        stat_name = "t"
        test_title = "Student's Two-Sample t-test"
        df_val = n1 + n2 - 2
        effect_size = calculate_cohens_d(s1, s2, paired=False)
        ci = calculate_mean_diff_ci(s1, s2, alpha=alpha, equal_var=True)
        if not homo.passed:
            warnings.append("Homogeneity of variance violated (Levene p < alpha). Welch's t-test is recommended.")
    else:  # Welch's t-test (default)
        stat, p_val = stats.ttest_ind(s1, s2, equal_var=False)
        stat_name = "Welch t"
        test_title = "Welch's Two-Sample t-test"

        # Welch-Satterthwaite df
        var1, var2 = float(s1.var(ddof=1)), float(s2.var(ddof=1))
        vn1, vn2 = var1 / n1, var2 / n2
        denom = (vn1**2) / (n1 - 1) + (vn2**2) / (n2 - 1)
        df_val = round(float((vn1 + vn2) ** 2 / denom), 2) if denom > 0 else (n1 + n2 - 2)

        effect_size = calculate_cohens_d(s1, s2, paired=False)
        ci = calculate_mean_diff_ci(s1, s2, alpha=alpha, equal_var=False)

    stat_val = float(stat) if not np.isnan(stat) else None
    p_val_float = float(p_val) if not np.isnan(p_val) else None
    is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

    ci_str = f", 95% CI: [{ci.lower:.4f}, {ci.upper:.4f}]" if ci and ci.lower is not None else ""
    statement = (
        f"{test_title} comparing '{g1_label}' (N={n1}) and '{g2_label}' (N={n2}) returned "
        f"{stat_name} = {stat_val:.4f}, p = {p_val_float:.4f} at α = {alpha} "
        f"(df = {df_val}{ci_str}, Effect Size: {effect_size.interpretation})."
    )

    return StatisticalAnalysisResult(
        test_name=test_title,
        category=AnalysisCategory.TWO_GROUP,
        method=method,
        variables={
            "value_column": value_column,
            "group_1": g1_label,
            "group_2": g2_label,
            "n_1": n1,
            "n_2": n2,
        },
        statistic_name=stat_name,
        statistic_value=round(stat_val, 4) if stat_val is not None else None,
        p_value=round(p_val_float, 4) if p_val_float is not None else None,
        df=df_val,
        alpha=alpha,
        is_significant=is_sig,
        sample_size={g1_label: n1, g2_label: n2},
        effect_size=effect_size,
        confidence_interval=ci,
        assumptions=assumptions,
        warnings=warnings,
        statement=statement,
    )
