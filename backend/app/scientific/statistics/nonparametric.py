from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.effect_sizes import (
    calculate_epsilon_squared,
    calculate_rank_biserial,
)
from app.scientific.statistics.models import (
    AnalysisCategory,
    PostHocMethod,
    PostHocResult,
    StatisticalAnalysisResult,
    StatisticalMethod,
)


def run_nonparametric_group_comparison(
    df: pd.DataFrame,
    value_column: str,
    group_column: str | None = None,
    value_column_2: str | None = None,
    method: StatisticalMethod = StatisticalMethod.MANN_WHITNEY,
    alpha: float = 0.05,
    post_hoc_method: PostHocMethod = PostHocMethod.BONFERRONI,
    paired: bool = False,
) -> StatisticalAnalysisResult:
    """Executes non-parametric group comparisons (Mann-Whitney U, Wilcoxon Signed-Rank, or Kruskal-Wallis)."""
    warnings = []

    if method == StatisticalMethod.KRUSKAL_WALLIS:
        if not group_column:
            raise ScientificValidationError("Kruskal-Wallis test requires a 'group_column'.")
        if group_column not in df.columns:
            raise ScientificValidationError(f"Group column '{group_column}' not found.")
        if value_column not in df.columns:
            raise ScientificValidationError(f"Value column '{value_column}' not found.")

        clean_df = df[[value_column, group_column]].dropna().copy()
        clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
        clean_df = clean_df.dropna()

        groups = sorted(clean_df[group_column].unique())
        if len(groups) < 2:
            raise ScientificValidationError(
                f"Kruskal-Wallis requires at least 2 unique groups in '{group_column}'. Found {len(groups)}."
            )

        group_series_list = [clean_df[clean_df[group_column] == g][value_column] for g in groups]
        sample_sizes = {str(g): len(s) for g, s in zip(groups, group_series_list, strict=False)}

        for g_label, n in sample_sizes.items():
            if n < 2:
                raise ScientificValidationError(
                    f"Group '{g_label}' has insufficient sample size (N={n}). "
                    "Minimum 2 observations per group required."
                )

        h_stat, p_val = stats.kruskal(*group_series_list)
        total_n = sum(sample_sizes.values())
        stat_name = "H"
        test_title = "Kruskal-Wallis H-test"
        df_val = len(groups) - 1

        effect_size = calculate_epsilon_squared(float(h_stat), total_n)

        # Post-hoc pairwise Dunn/Mann-Whitney with Bonferroni/Holm correction
        post_hoc_results = []
        if post_hoc_method != PostHocMethod.NONE:
            pairs = list(combinations(groups, 2))
            raw_p_vals = []
            pair_data = []

            for g1, g2 in pairs:
                s1 = clean_df[clean_df[group_column] == g1][value_column]
                s2 = clean_df[clean_df[group_column] == g2][value_column]
                u_res = stats.mannwhitneyu(s1, s2, alternative="two-sided")
                raw_p_vals.append(float(u_res.pvalue))
                pair_data.append((str(g1), str(g2), float(u_res.statistic), float(u_res.pvalue)))

            n_comp = len(pairs)
            if post_hoc_method == PostHocMethod.BONFERRONI:
                adj_p_vals = [min(1.0, p * n_comp) for p in raw_p_vals]
                corr_label = "Dunn-Bonferroni"
            else:  # Holm
                sorted_idx = np.argsort(raw_p_vals)
                adj_p = np.zeros(n_comp)
                cum_max = 0.0
                for i, idx in enumerate(sorted_idx):
                    multiplier = n_comp - i
                    val = min(1.0, raw_p_vals[idx] * multiplier)
                    cum_max = max(cum_max, val)
                    adj_p[idx] = cum_max
                adj_p_vals = list(adj_p)
                corr_label = "Dunn-Holm"

            for (g1, g2, u_val, p_raw), p_adj in zip(pair_data, adj_p_vals, strict=False):
                post_hoc_results.append(
                    PostHocResult(
                        group1=g1,
                        group2=g2,
                        statistic=round(u_val, 4),
                        p_raw=round(p_raw, 4),
                        p_adjusted=round(p_adj, 4),
                        correction_method=corr_label,
                        is_significant=bool(p_adj < alpha),
                    )
                )

        f_stat_val = float(h_stat) if not np.isnan(h_stat) else None
        p_val_float = float(p_val) if not np.isnan(p_val) else None
        is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

        statement = (
            f"Kruskal-Wallis H-test across {len(groups)} groups ('{group_column}') for '{value_column}' "
            f"returned H = {f_stat_val:.4f}, p = {p_val_float:.4f} at α = {alpha} "
            f"(df = {df_val}, Effect Size: {effect_size.interpretation}, epsilon^2 = {effect_size.value})."
        )

        return StatisticalAnalysisResult(
            test_name=test_title,
            category=AnalysisCategory.NONPARAMETRIC,
            method=method,
            variables={
                "value_column": value_column,
                "group_column": group_column,
                "groups": [str(g) for g in groups],
            },
            statistic_name=stat_name,
            statistic_value=round(f_stat_val, 4) if f_stat_val is not None else None,
            p_value=round(p_val_float, 4) if p_val_float is not None else None,
            df=df_val,
            alpha=alpha,
            is_significant=is_sig,
            sample_size=sample_sizes,
            effect_size=effect_size,
            post_hoc=post_hoc_results,
            warnings=warnings,
            statement=statement,
        )

    # 2-Group Non-Parametric (Mann-Whitney U or Wilcoxon Signed-Rank)
    if group_column:
        clean_df = df[[value_column, group_column]].dropna().copy()
        clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
        clean_df = clean_df.dropna()

        unique_groups = list(clean_df[group_column].unique())
        if len(unique_groups) != 2:
            raise ScientificValidationError(
                f"Group column '{group_column}' must contain exactly 2 unique groups for two-group test."
            )

        g1_label, g2_label = str(unique_groups[0]), str(unique_groups[1])
        s1 = clean_df[clean_df[group_column] == unique_groups[0]][value_column]
        s2 = clean_df[clean_df[group_column] == unique_groups[1]][value_column]
    elif value_column_2:
        clean_df = df[[value_column, value_column_2]].dropna().copy()
        clean_df[value_column] = pd.to_numeric(clean_df[value_column], errors="coerce")
        clean_df[value_column_2] = pd.to_numeric(clean_df[value_column_2], errors="coerce")
        clean_df = clean_df.dropna()

        g1_label, g2_label = value_column, value_column_2
        s1 = clean_df[value_column]
        s2 = clean_df[value_column_2]
    else:
        raise ScientificValidationError("Either group_column or value_column_2 must be provided.")

    n1, n2 = len(s1), len(s2)
    if n1 < 2 or n2 < 2:
        raise ScientificValidationError(
            f"Insufficient sample size (Group 1 N={n1}, Group 2 N={n2}). Minimum 2 per group required."
        )

    if (method == StatisticalMethod.WILCOXON_SIGNED_RANK or paired) and n1 != n2:
        raise ScientificValidationError("Wilcoxon Signed-Rank test requires equal sample sizes (paired samples).")

    if method == StatisticalMethod.WILCOXON_SIGNED_RANK or paired:
        stat, p_val = stats.wilcoxon(s1, s2)
        stat_name = "W"
        test_title = "Wilcoxon Signed-Rank Test"
        effect_size = calculate_rank_biserial(float(stat), n1, n2)
    else:
        stat, p_val = stats.mannwhitneyu(s1, s2, alternative="two-sided")
        stat_name = "U"
        test_title = "Mann-Whitney U Test"
        effect_size = calculate_rank_biserial(float(stat), n1, n2)

    stat_val = float(stat) if not np.isnan(stat) else None
    p_val_float = float(p_val) if not np.isnan(p_val) else None
    is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

    statement = (
        f"{test_title} comparing '{g1_label}' (N={n1}) and '{g2_label}' (N={n2}) returned "
        f"{stat_name} = {stat_val:.4f}, p = {p_val_float:.4f} at α = {alpha} "
        f"(Effect Size: {effect_size.interpretation}, Rank-Biserial r = {effect_size.value})."
    )

    return StatisticalAnalysisResult(
        test_name=test_title,
        category=AnalysisCategory.NONPARAMETRIC,
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
        df=None,
        alpha=alpha,
        is_significant=is_sig,
        sample_size={g1_label: n1, g2_label: n2},
        effect_size=effect_size,
        warnings=warnings,
        statement=statement,
    )
