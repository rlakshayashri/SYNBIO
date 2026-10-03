import numpy as np
import pandas as pd
from scipy import stats

from app.scientific.statistics.models import EffectSizeResult


def calculate_cohens_d(group1: pd.Series, group2: pd.Series, paired: bool = False) -> EffectSizeResult:
    """Calculates Cohen's d effect size for independent or paired two-group comparisons."""
    s1 = pd.to_numeric(group1, errors="coerce").dropna()
    s2 = pd.to_numeric(group2, errors="coerce").dropna()

    if len(s1) < 2 or len(s2) < 2:
        return EffectSizeResult(name="Cohen's d", value=None, interpretation="Insufficient sample size")

    if paired:
        if len(s1) != len(s2):
            return EffectSizeResult(
                name="Cohen's d",
                value=None,
                interpretation="Unequal sample sizes for paired test",
            )
        diff = s1.values - s2.values
        sd_diff = float(np.std(diff, ddof=1))
        if sd_diff == 0:
            return EffectSizeResult(name="Cohen's d", value=0.0, interpretation="negligible")
        d = float(np.mean(diff) / sd_diff)
    else:
        n1, n2 = len(s1), len(s2)
        var1, var2 = float(s1.var(ddof=1)), float(s2.var(ddof=1))
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return EffectSizeResult(name="Cohen's d", value=0.0, interpretation="negligible")

        d = float((s1.mean() - s2.mean()) / pooled_std)

    abs_d = abs(d)
    if abs_d < 0.2:
        interp = "negligible"
    elif abs_d < 0.5:
        interp = "small"
    elif abs_d < 0.8:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name="Cohen's d", value=round(d, 4), interpretation=interp)


def calculate_eta_squared(groups_data: list[pd.Series]) -> EffectSizeResult:
    """Calculates Eta-squared (eta^2) effect size for One-Way ANOVA."""
    clean_groups = [pd.to_numeric(g, errors="coerce").dropna().values for g in groups_data]
    clean_groups = [g for g in clean_groups if len(g) > 0]

    if len(clean_groups) < 2:
        return EffectSizeResult(name="Eta-squared (eta^2)", value=None, interpretation="Invalid groups")

    all_data = np.concatenate(clean_groups)
    grand_mean = np.mean(all_data)

    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in clean_groups)
    ss_total = sum((x - grand_mean) ** 2 for x in all_data)

    if ss_total == 0:
        return EffectSizeResult(name="Eta-squared (eta^2)", value=0.0, interpretation="negligible")

    eta_sq = float(ss_between / ss_total)
    if eta_sq < 0.01:
        interp = "negligible"
    elif eta_sq < 0.06:
        interp = "small"
    elif eta_sq < 0.14:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name="Eta-squared (eta^2)", value=round(eta_sq, 4), interpretation=interp)


def calculate_rank_biserial(u_stat: float, n1: int, n2: int) -> EffectSizeResult:
    """Calculates Rank-Biserial correlation (r) effect size for Mann-Whitney U test."""
    if n1 * n2 == 0:
        return EffectSizeResult(name="Rank-Biserial r", value=None, interpretation="Zero sample size")

    # r = 1 - (2U / (N1 * N2))
    r = float(1.0 - (2.0 * u_stat) / (n1 * n2))
    abs_r = abs(r)

    if abs_r < 0.1:
        interp = "negligible"
    elif abs_r < 0.3:
        interp = "small"
    elif abs_r < 0.5:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name="Rank-Biserial r", value=round(r, 4), interpretation=interp)


def calculate_wilcoxon_r(z_stat: float | None, p_value: float | None, n_pairs: int) -> EffectSizeResult:
    """Calculates standardized matched-pairs effect size r = |Z| / sqrt(N) for Wilcoxon Signed-Rank test.

    References:
        Rosenthal, R. (1991). Meta-analytic procedures for social research. Sage.
        Tomczak, M., & Tomczak, E. (2014). The need to report effect size estimates in
        neuropsychological research. Trends in Sport Sciences, 1(21), 19-25.
    """
    if n_pairs <= 0:
        return EffectSizeResult(name="Wilcoxon r", value=None, interpretation="Invalid sample size")

    if z_stat is not None and not np.isnan(z_stat):
        z = abs(float(z_stat))
    elif p_value is not None and 0.0 < p_value < 1.0:
        z = abs(float(stats.norm.ppf(1.0 - p_value / 2.0)))
    else:
        z = 0.0

    r = float(z / np.sqrt(n_pairs))
    abs_r = abs(r)

    if abs_r < 0.1:
        interp = "negligible"
    elif abs_r < 0.3:
        interp = "small"
    elif abs_r < 0.5:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name="Wilcoxon r", value=round(r, 4), interpretation=interp)


def calculate_epsilon_squared(h_stat: float, total_n: int) -> EffectSizeResult:
    """Calculates Epsilon-squared (epsilon^2) effect size for Kruskal-Wallis test."""
    if total_n <= 1:
        return EffectSizeResult(name="Epsilon-squared (epsilon^2)", value=None, interpretation="Invalid N")

    # epsilon^2 = (H * (N + 1)) / (N^2 - 1)
    eps_sq = float((h_stat * (total_n + 1)) / (total_n**2 - 1))
    eps_sq = max(0.0, min(1.0, eps_sq))

    if eps_sq < 0.01:
        interp = "negligible"
    elif eps_sq < 0.06:
        interp = "small"
    elif eps_sq < 0.14:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name="Epsilon-squared (epsilon^2)", value=round(eps_sq, 4), interpretation=interp)


def interpret_correlation_effect_size(r: float, name: str = "Pearson r") -> EffectSizeResult:
    """Classifies correlation coefficient magnitude into standard effect size tiers."""
    abs_r = abs(r)
    if abs_r < 0.1:
        interp = "negligible"
    elif abs_r < 0.3:
        interp = "small"
    elif abs_r < 0.5:
        interp = "medium"
    else:
        interp = "large"

    return EffectSizeResult(name=name, value=round(r, 4), interpretation=interp)
