from typing import Any

import pandas as pd

from app.core.exceptions import ScientificValidationError
from app.schemas.comparison import GroupDataSummary
from app.scientific.statistics.anova import run_anova_analysis
from app.scientific.statistics.descriptive import calculate_descriptive_statistics
from app.scientific.statistics.group_comparison import run_two_group_comparison
from app.scientific.statistics.models import (
    PostHocMethod,
    StatisticalAnalysisResult,
    StatisticalMethod,
)
from app.scientific.statistics.nonparametric import run_nonparametric_group_comparison


def execute_experimental_comparison(
    df: pd.DataFrame,
    measurement_column: str,
    comparison_type: str = "two_group",
    group_column: str | None = None,
    group_a_code: str | None = None,
    group_b_code: str | None = None,
    method: StatisticalMethod = StatisticalMethod.WELCH_TTEST,
    alpha: float = 0.05,
    paired: bool = False,
    post_hoc_method: PostHocMethod = PostHocMethod.NONE,
) -> dict[str, Any]:
    """Orchestrates group data preparation, descriptive statistics, and statistical comparison.

    Strictly preserves DataFrame immutability and delegates calculations to the Module 5 engine.
    """
    if measurement_column not in df.columns:
        raise ScientificValidationError(f"Measurement column '{measurement_column}' not found in dataset.")

    # 1. Filter DataFrame if specific group codes are requested for a two-group comparison
    sub_df = df.copy()
    if group_column:
        if group_column not in sub_df.columns:
            raise ScientificValidationError(f"Group column '{group_column}' not found in dataset.")

        if group_a_code and group_b_code and comparison_type == "two_group":
            sub_df = sub_df[sub_df[group_column].astype(str).isin([str(group_a_code), str(group_b_code)])].copy()

    # 2. Extract Group Data Summaries
    group_summaries: list[GroupDataSummary] = []
    if group_column:
        unique_groups = sub_df[group_column].dropna().unique()
        for g in sorted(unique_groups, key=lambda x: str(x)):
            g_str = str(g)
            group_rows = sub_df[sub_df[group_column] == g]
            total_count = len(group_rows)
            valid_series = pd.to_numeric(group_rows[measurement_column], errors="coerce").dropna()
            valid_count = len(valid_series)
            missing_count = total_count - valid_count

            # Calculate descriptive stats using Module 3 function
            g_df = pd.DataFrame({measurement_column: valid_series})
            desc_stats_res = calculate_descriptive_statistics(g_df)

            group_summaries.append(
                GroupDataSummary(
                    group_name=g_str,
                    group_code=g_str,
                    is_control=False,
                    sample_size_total=total_count,
                    sample_size_valid=valid_count,
                    missing_count=missing_count,
                    descriptive_stats=desc_stats_res,
                )
            )
    else:
        total_count = len(sub_df)
        valid_series = pd.to_numeric(sub_df[measurement_column], errors="coerce").dropna()
        valid_count = len(valid_series)
        missing_count = total_count - valid_count
        g_df = pd.DataFrame({measurement_column: valid_series})
        desc_stats_res = calculate_descriptive_statistics(g_df)

        group_summaries.append(
            GroupDataSummary(
                group_name=measurement_column,
                group_code=measurement_column,
                is_control=False,
                sample_size_total=total_count,
                sample_size_valid=valid_count,
                missing_count=missing_count,
                descriptive_stats=desc_stats_res,
            )
        )

    # 3. Delegate to Module 5 Statistical Engine
    if comparison_type == "anova" or method in [StatisticalMethod.ONE_WAY_ANOVA, StatisticalMethod.WELCH_ANOVA]:
        if not group_column:
            raise ScientificValidationError("ANOVA comparison requires a group_column.")
        stat_result: StatisticalAnalysisResult = run_anova_analysis(
            sub_df,
            value_column=measurement_column,
            group_column=group_column,
            method=method,
            alpha=alpha,
            post_hoc_method=post_hoc_method,
        )
    elif comparison_type == "nonparametric" or method in [
        StatisticalMethod.MANN_WHITNEY,
        StatisticalMethod.WILCOXON_SIGNED_RANK,
        StatisticalMethod.KRUSKAL_WALLIS,
    ]:
        stat_result = run_nonparametric_group_comparison(
            sub_df,
            value_column=measurement_column,
            group_column=group_column,
            method=method,
            alpha=alpha,
            post_hoc_method=post_hoc_method,
            paired=paired,
        )
    else:
        stat_result = run_two_group_comparison(
            sub_df,
            value_column=measurement_column,
            group_column=group_column,
            method=method,
            alpha=alpha,
            paired=paired,
        )

    return {
        "group_summaries": group_summaries,
        "statistical_result": stat_result,
    }
