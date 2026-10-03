import numpy as np
import pandas as pd
from scipy import stats

from app.scientific.statistics.models import ConfidenceIntervalResult


def calculate_mean_diff_ci(
    group1: pd.Series,
    group2: pd.Series,
    alpha: float = 0.05,
    equal_var: bool = True,
    paired: bool = False,
) -> ConfidenceIntervalResult:
    """Calculates confidence interval for mean difference between two groups."""
    s1 = pd.to_numeric(group1, errors="coerce").dropna()
    s2 = pd.to_numeric(group2, errors="coerce").dropna()
    confidence_level = 1.0 - alpha

    if len(s1) < 2 or len(s2) < 2:
        return ConfidenceIntervalResult(level=confidence_level, lower=None, upper=None, metric="mean difference")

    if paired:
        if len(s1) != len(s2):
            return ConfidenceIntervalResult(level=confidence_level, lower=None, upper=None, metric="mean difference")
        diff = s1.values - s2.values
        n = len(diff)
        mean_diff = float(np.mean(diff))
        sd_diff = float(np.std(diff, ddof=1))
        se = sd_diff / np.sqrt(n) if n > 0 else 0.0
        df = n - 1
    else:
        n1, n2 = len(s1), len(s2)
        mean_diff = float(s1.mean() - s2.mean())
        var1, var2 = float(s1.var(ddof=1)), float(s2.var(ddof=1))

        if equal_var:
            df = n1 + n2 - 2
            pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / df
            se = np.sqrt(pooled_var * (1.0 / n1 + 1.0 / n2))
        else:
            # Welch-Satterthwaite df
            vn1, vn2 = var1 / n1, var2 / n2
            se = np.sqrt(vn1 + vn2)
            denom = (vn1**2) / (n1 - 1) + (vn2**2) / (n2 - 1)
            df = (vn1 + vn2) ** 2 / denom if denom > 0 else (n1 + n2 - 2)

    if se == 0 or df <= 0:
        return ConfidenceIntervalResult(
            level=confidence_level,
            lower=round(mean_diff, 4),
            upper=round(mean_diff, 4),
            metric="mean difference",
        )

    t_crit = stats.t.ppf(1.0 - alpha / 2.0, df)
    margin = float(t_crit * se)

    lower = round(mean_diff - margin, 4)
    upper = round(mean_diff + margin, 4)

    return ConfidenceIntervalResult(level=confidence_level, lower=lower, upper=upper, metric="mean difference")


def calculate_pearson_r_ci(r: float, n: int, alpha: float = 0.05) -> ConfidenceIntervalResult:
    """Calculates Fisher z-transformation confidence interval for Pearson correlation r."""
    confidence_level = 1.0 - alpha

    if n <= 3 or abs(r) >= 1.0:
        return ConfidenceIntervalResult(level=confidence_level, lower=None, upper=None, metric="Pearson r")

    try:
        # Fisher z transformation
        z = np.arctanh(r)
        se = 1.0 / np.sqrt(n - 3)
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)

        z_lower = z - z_crit * se
        z_upper = z + z_crit * se

        r_lower = float(np.tanh(z_lower))
        r_upper = float(np.tanh(z_upper))

        return ConfidenceIntervalResult(
            level=confidence_level,
            lower=round(r_lower, 4),
            upper=round(r_upper, 4),
            metric="Pearson r",
        )
    except Exception:
        return ConfidenceIntervalResult(level=confidence_level, lower=None, upper=None, metric="Pearson r")
