from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from app.scientific.statistics.models import PostHocMethod, PostHocResult


def run_post_hoc_tukey(df: pd.DataFrame, value_col: str, group_col: str, alpha: float = 0.05) -> list[PostHocResult]:
    """Executes Tukey HSD post-hoc test for One-Way ANOVA pairwise group comparisons."""
    clean_df = df[[value_col, group_col]].dropna()
    clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors="coerce")
    clean_df = clean_df.dropna()

    if len(clean_df[group_col].unique()) < 2:
        return []

    try:
        tukey_res = pairwise_tukeyhsd(endog=clean_df[value_col], groups=clean_df[group_col], alpha=alpha)

        results = []
        for row in tukey_res._results_table.data[1:]:
            g1, g2, meandiff, p_adj, lower, upper, reject = row
            p_adj_float = float(p_adj) if not np.isnan(p_adj) else None
            is_sig = bool(reject)

            results.append(
                PostHocResult(
                    group1=str(g1),
                    group2=str(g2),
                    statistic=round(float(meandiff), 4),
                    p_raw=p_adj_float,  # Tukey computes familywise p directly
                    p_adjusted=p_adj_float,
                    correction_method="Tukey HSD",
                    is_significant=is_sig,
                )
            )
        return results
    except Exception:
        return []


def run_post_hoc_pairwise_ttest(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    method: PostHocMethod = PostHocMethod.BONFERRONI,
    alpha: float = 0.05,
) -> list[PostHocResult]:
    """Executes pairwise Welch/Student t-tests with Bonferroni or Holm correction."""
    clean_df = df[[value_col, group_col]].dropna()
    clean_df[value_col] = pd.to_numeric(clean_df[value_col], errors="coerce")
    clean_df = clean_df.dropna()

    groups = sorted(clean_df[group_col].unique())
    if len(groups) < 2:
        return []

    pairs = list(combinations(groups, 2))
    raw_p_values = []
    pair_details = []

    for g1, g2 in pairs:
        s1 = clean_df[clean_df[group_col] == g1][value_col]
        s2 = clean_df[clean_df[group_col] == g2][value_col]

        if len(s1) >= 2 and len(s2) >= 2:
            stat, p_val = stats.ttest_ind(s1, s2, equal_var=False)
            stat_val = float(stat) if not np.isnan(stat) else 0.0
            p_val_float = float(p_val) if not np.isnan(p_val) else 1.0
        else:
            stat_val = 0.0
            p_val_float = 1.0

        raw_p_values.append(p_val_float)
        pair_details.append((str(g1), str(g2), stat_val, p_val_float))

    n_comp = len(pairs)
    adjusted_p_values = []

    if method == PostHocMethod.BONFERRONI:
        adjusted_p_values = [min(1.0, p * n_comp) for p in raw_p_values]
        corr_label = "Bonferroni"
    elif method == PostHocMethod.HOLM:
        # Holm-Bonferroni step-down adjustment
        sorted_indices = np.argsort(raw_p_values)
        adj_p = np.zeros(n_comp)
        cum_max = 0.0
        for i, idx in enumerate(sorted_indices):
            multiplier = n_comp - i
            val = min(1.0, raw_p_values[idx] * multiplier)
            cum_max = max(cum_max, val)
            adj_p[idx] = cum_max
        adjusted_p_values = list(adj_p)
        corr_label = "Holm-Bonferroni"
    else:
        adjusted_p_values = raw_p_values
        corr_label = "Unadjusted"

    results = []
    for (g1, g2, stat_val, p_raw), p_adj in zip(pair_details, adjusted_p_values, strict=False):
        results.append(
            PostHocResult(
                group1=g1,
                group2=g2,
                statistic=round(stat_val, 4),
                p_raw=round(p_raw, 4),
                p_adjusted=round(p_adj, 4),
                correction_method=corr_label,
                is_significant=bool(p_adj < alpha),
            )
        )
    return results
