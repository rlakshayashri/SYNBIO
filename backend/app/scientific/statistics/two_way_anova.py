import math

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import optimize, stats
from statsmodels.stats.anova import anova_lm

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.assumptions import check_homogeneity, check_normality
from app.scientific.statistics.factorial_models import (
    AnovaEffectResult,
    FactorialAnalysisOptions,
    SimpleEffectResult,
    TwoWayAnovaResult,
)
from app.scientific.statistics.models import AssumptionResult, PostHocMethod, PostHocResult
from app.scientific.statistics.multiple_comparison import (
    run_post_hoc_pairwise_ttest,
    run_post_hoc_tukey,
)


def validate_factorial_inputs(
    df: pd.DataFrame,
    response_col: str,
    factor_a_col: str,
    factor_b_col: str,
    options: FactorialAnalysisOptions,
) -> tuple[pd.DataFrame, dict[str, int], list[str]]:
    """Validates dataframe columns, types, design completeness, and missing data for Two-Way ANOVA."""
    if not isinstance(df, pd.DataFrame):
        raise ScientificValidationError(f"Input data must be a pandas DataFrame, got {type(df).__name__}.")

    if len(df) == 0:
        raise ScientificValidationError("Dataset is empty. At least 4 observations are required for Two-Way ANOVA.")

    # 1. Column existence checks
    for col_name, label in [
        (response_col, "Response"),
        (factor_a_col, "Factor A"),
        (factor_b_col, "Factor B"),
    ]:
        if col_name not in df.columns:
            raise ScientificValidationError(f"{label} column '{col_name}' was not found in the dataset.")

    # 2. Identical factor selection check
    if factor_a_col == factor_b_col:
        raise ScientificValidationError(
            f"Factor A and Factor B cannot be the identical column ('{factor_a_col}'). Distinct factors are required."
        )

    # 3. Missing and non-finite value accounting
    raw_response = df[response_col]
    raw_fa = df[factor_a_col]
    raw_fb = df[factor_b_col]

    numeric_response = pd.to_numeric(raw_response, errors="coerce")
    n_non_numeric_or_missing_resp = int(numeric_response.isna().sum())
    n_infinite_resp = int(np.isinf(numeric_response).sum())
    n_missing_fa = int(raw_fa.isna().sum() + (raw_fa.astype(str).str.strip() == "").sum())
    n_missing_fb = int(raw_fb.isna().sum() + (raw_fb.astype(str).str.strip() == "").sum())

    exclusion_reasons = {
        "missing_or_non_numeric_response": n_non_numeric_or_missing_resp,
        "infinite_response": n_infinite_resp,
        "missing_factor_a": n_missing_fa,
        "missing_factor_b": n_missing_fb,
    }

    # Filter to valid observations
    valid_mask = (
        numeric_response.notna()
        & ~np.isinf(numeric_response)
        & raw_fa.notna()
        & (raw_fa.astype(str).str.strip() != "")
        & raw_fb.notna()
        & (raw_fb.astype(str).str.strip() != "")
    )
    clean_df = df[valid_mask].copy()

    # Cast response to float and factors to string
    clean_df[response_col] = numeric_response[valid_mask].astype(float)
    clean_df[factor_a_col] = clean_df[factor_a_col].astype(str).str.strip()
    clean_df[factor_b_col] = clean_df[factor_b_col].astype(str).str.strip()

    excluded_rows_count = len(df) - len(clean_df)
    warnings: list[str] = []
    if excluded_rows_count > 0:
        warnings.append(
            f"Excluded {excluded_rows_count} observations with missing, non-numeric, or non-finite values."
        )

    # 4. Valid rows count
    n_valid = len(clean_df)
    if n_valid < 4:
        raise ScientificValidationError(
            f"Insufficient valid observations (N={n_valid}). Minimum 4 observations required for Two-Way ANOVA."
        )

    # 5. Check factor levels
    levels_a = sorted(clean_df[factor_a_col].unique())
    levels_b = sorted(clean_df[factor_b_col].unique())

    if len(levels_a) < 2:
        raise ScientificValidationError(
            f"Factor A ('{factor_a_col}') requires at least 2 distinct observed levels. "
            f"Found {len(levels_a)}: {levels_a}."
        )
    if len(levels_b) < 2:
        raise ScientificValidationError(
            f"Factor B ('{factor_b_col}') requires at least 2 distinct observed levels. "
            f"Found {len(levels_b)}: {levels_b}."
        )

    # 6. Check for empty cells (incomplete factorial design)
    crosstab = pd.crosstab(clean_df[factor_a_col], clean_df[factor_b_col])
    empty_cells = [
        f"{a} × {b}" for a in levels_a for b in levels_b if crosstab.loc[a, b] == 0
    ]
    if empty_cells:
        raise ScientificValidationError(
            f"Factorial design is incomplete. The following factor-level combinations have 0 observations: "
            f"{', '.join(empty_cells)}. Full factorial interaction cannot be estimated without all cell "
            f"combinations observed."
        )

    # 7. Check residual degrees of freedom
    total_cell_params = len(levels_a) * len(levels_b)
    df_residual = n_valid - total_cell_params
    if df_residual <= 0:
        raise ScientificValidationError(
            f"Insufficient residual degrees of freedom (N={n_valid}, model parameters={total_cell_params}, "
            f"df_residual={df_residual}). Replication is required to estimate experimental error in Two-Way ANOVA."
        )

    return clean_df, exclusion_reasons, warnings


def calculate_partial_eta_squared(
    ss_effect: float,
    ss_error: float,
    df_effect: float,
    df_error: float,
    confidence_level: float = 0.95,
) -> tuple[float, list[float] | None, str]:
    """Calculates partial eta-squared (eta_p^2), qualitative interpretation, and inversion confidence intervals."""
    denom = ss_effect + ss_error
    if denom <= 0:
        return 0.0, None, "negligible"

    eta_p = float(ss_effect / denom)
    eta_p = max(0.0, min(1.0, eta_p))

    # Qualitative interpretation (Cohen 1988 guidelines for partial eta-squared)
    if eta_p < 0.01:
        interpretation = "negligible"
    elif eta_p < 0.06:
        interpretation = "small"
    elif eta_p < 0.14:
        interpretation = "medium"
    else:
        interpretation = "large"

    # Confidence interval via Noncentral F distribution inversion (Smithson 2001)
    ci: list[float] | None = None
    if df_effect > 0 and df_error > 0 and ss_error > 0:
        try:
            ms_effect = ss_effect / df_effect
            ms_error = ss_error / df_error
            f_stat = ms_effect / ms_error

            if f_stat > 0 and not math.isnan(f_stat) and not math.isinf(f_stat):
                alpha = 1.0 - confidence_level
                p_lower = alpha / 2.0
                p_upper = 1.0 - (alpha / 2.0)

                # Lower bound lambda
                if stats.ncf.cdf(f_stat, df_effect, df_error, 0.0) < p_upper:
                    lam_low = 0.0
                else:
                    sol_low = optimize.root_scalar(
                        lambda lam: stats.ncf.cdf(f_stat, df_effect, df_error, lam) - p_upper,
                        bracket=[0.0, max(100.0, f_stat * 10)],
                        method="brentq",
                    )
                    lam_low = max(0.0, sol_low.root)

                # Upper bound lambda
                bracket_high = max(500.0, f_stat * 20.0)
                # Expand bracket if needed
                while stats.ncf.cdf(f_stat, df_effect, df_error, bracket_high) > p_lower and bracket_high < 10000.0:
                    bracket_high *= 2.0

                sol_up = optimize.root_scalar(
                    lambda lam: stats.ncf.cdf(f_stat, df_effect, df_error, lam) - p_lower,
                    bracket=[0.0, bracket_high],
                    method="brentq",
                )
                lam_up = max(lam_low, sol_up.root)

                eta_low = lam_low / (lam_low + df_error)
                eta_up = lam_up / (lam_up + df_error)

                ci = [
                    round(max(0.0, min(1.0, float(eta_low))), 4),
                    round(max(0.0, min(1.0, float(eta_up))), 4),
                ]
        except Exception:
            ci = None

    return round(eta_p, 4), ci, interpretation


def compute_two_way_anova(
    df: pd.DataFrame,
    response_column: str,
    factor_a_column: str,
    factor_b_column: str,
    options: FactorialAnalysisOptions | None = None,
) -> TwoWayAnovaResult:
    """Executes pure scientific Two-Way ANOVA with sum-to-zero contrasts (Type III SS), diagnostics, and post-hocs."""
    if options is None:
        options = FactorialAnalysisOptions()

    # 1. Validate inputs and clean missing/invalid data
    clean_df, exclusion_reasons, warnings = validate_factorial_inputs(
        df, response_column, factor_a_column, factor_b_column, options
    )
    excluded_rows_count = len(df) - len(clean_df)

    alpha = options.alpha
    levels_a = sorted(clean_df[factor_a_column].unique())
    levels_b = sorted(clean_df[factor_b_column].unique())

    # Cell sample counts and balance assessment
    crosstab = pd.crosstab(clean_df[factor_a_column], clean_df[factor_b_column])
    cell_sample_sizes: dict[str, int] = {}
    for a in levels_a:
        for b in levels_b:
            cell_sample_sizes[f"{a} × {b}"] = int(crosstab.loc[a, b])

    cell_counts_list = list(cell_sample_sizes.values())
    min_cell_size = min(cell_counts_list)
    max_cell_size = max(cell_counts_list)
    is_balanced = min_cell_size == max_cell_size
    design_balance = "balanced" if is_balanced else "unbalanced_estimable"

    if not is_balanced:
        warnings.append(
            f"Unbalanced design detected (cell sizes range from {min_cell_size} to {max_cell_size}). "
            f"Type III sums of squares with sum-to-zero contrasts ensures unconfounded main effect tests."
        )

    # 2. Fit Ordinary Least Squares model with Sum contrasts (deviation coding)
    model_df = clean_df.copy()
    model_df["__y"] = clean_df[response_column]
    model_df["__fa"] = clean_df[factor_a_column]
    model_df["__fb"] = clean_df[factor_b_column]

    formula = "__y ~ C(__fa, Sum) * C(__fb, Sum)"
    model = smf.ols(formula, data=model_df).fit()

    # Compute Type III ANOVA table
    anova_table = anova_lm(model, typ=3)

    # Extract residual error term
    residual_row = anova_table.loc["Residual"]
    ss_error = float(residual_row["sum_sq"])
    df_error = float(residual_row["df"])
    ms_error = ss_error / df_error if df_error > 0 else 0.0

    # 3. Extract effects and compute partial eta-squared
    term_map = {
        "C(__fa, Sum)": factor_a_column,
        "C(__fb, Sum)": factor_b_column,
        "C(__fa, Sum):C(__fb, Sum)": f"{factor_a_column} × {factor_b_column}",
    }

    effects: dict[str, AnovaEffectResult] = {}
    for term, label in term_map.items():
        if term in anova_table.index:
            row = anova_table.loc[term]
            ss_eff = float(row["sum_sq"])
            df_eff = float(row["df"])
            f_stat = float(row["F"]) if not np.isnan(row["F"]) else None
            p_val = float(row["PR(>F)"]) if not np.isnan(row["PR(>F)"]) else None
            is_sig = bool(p_val < alpha) if p_val is not None else False
            ms_eff = ss_eff / df_eff if df_eff > 0 else None

            eta_p, eta_p_ci, interp = calculate_partial_eta_squared(
                ss_eff, ss_error, df_eff, df_error, confidence_level=options.confidence_level
            )

            effects[label] = AnovaEffectResult(
                effect_name=label,
                df=round(df_eff, 4),
                sum_sq=round(ss_eff, 4),
                mean_sq=round(ms_eff, 4) if ms_eff is not None else None,
                f_statistic=round(f_stat, 4) if f_stat is not None else None,
                p_value=round(p_val, 6) if p_val is not None else None,
                is_significant=is_sig,
                partial_eta_squared=eta_p,
                partial_eta_squared_ci=eta_p_ci,
                effect_size_interpretation=interp,
            )

    effects["Residual"] = AnovaEffectResult(
        effect_name="Residual",
        df=round(df_error, 4),
        sum_sq=round(ss_error, 4),
        mean_sq=round(ms_error, 4),
        f_statistic=None,
        p_value=None,
        is_significant=False,
        partial_eta_squared=None,
        partial_eta_squared_ci=None,
        effect_size_interpretation=None,
    )

    # 4. Assumption Diagnostics
    assumptions: list[AssumptionResult] = []

    # A. Residual normality
    residuals = model.resid
    normality_res = check_normality(residuals, variable_label="Model Residuals", alpha=alpha)
    assumptions.append(normality_res)
    if not normality_res.passed:
        warnings.append(
            f"Residual normality assumption violated ({normality_res.details}). "
            f"Caution advised for marginal p-value interpretations."
        )

    # B. Homogeneity of variance across cells
    cell_series_list = []
    cell_labels = []
    for a in levels_a:
        for b in levels_b:
            subset = clean_df[(clean_df[factor_a_column] == a) & (clean_df[factor_b_column] == b)][response_column]
            if len(subset) >= 2:
                cell_series_list.append(subset)
                cell_labels.append(f"{a} × {b}")

    homo_res = check_homogeneity(cell_series_list, cell_labels, alpha=alpha)
    assumptions.append(homo_res)
    if not homo_res.passed:
        warnings.append(
            f"Homogeneity of variance across factorial cells violated ({homo_res.details})."
        )

    # C. Influential observations (Cook's distance)
    try:
        influence = model.get_influence()
        cooks_d = influence.cooks_distance[0]
        n_obs = len(clean_df)
        cook_threshold = 4.0 / n_obs
        influential_count = int(np.sum(cooks_d > cook_threshold))
        max_cooks = float(np.max(cooks_d)) if len(cooks_d) > 0 else 0.0

        influence_passed = bool(max_cooks < 1.0)
        assumptions.append(
            AssumptionResult(
                name="Influential Observations (Cook's Distance)",
                statistic=round(max_cooks, 4),
                p_value=None,
                passed=influence_passed,
                details=(
                    f"Max Cook's D = {max_cooks:.4f} (Threshold 4/N={cook_threshold:.4f}). "
                    f"{influential_count} observation(s) exceed 4/N."
                ),
            )
        )
        if not influence_passed:
            warnings.append(
                f"Highly influential observations detected (Max Cook's Distance = {max_cooks:.4f} > 1.0)."
            )
    except Exception as exc:
        assumptions.append(
            AssumptionResult(
                name="Influential Observations",
                statistic=None,
                p_value=None,
                passed=True,
                details=f"Influence diagnostics could not be computed: {str(exc)}",
            )
        )

    # 5. Post-hoc Analysis and Simple Effects
    interaction_label = f"{factor_a_column} × {factor_b_column}"
    interaction_effect = effects.get(interaction_label)
    interaction_sig = bool(interaction_effect.is_significant) if interaction_effect else False

    post_hoc_comparisons: list[PostHocResult] = []
    simple_effects: list[SimpleEffectResult] = []

    def _format_p_statement(eff: AnovaEffectResult | None) -> str:
        if not eff or eff.p_value is None:
            return "p=N/A"
        if eff.p_value < 0.0001:
            return "p < 0.0001"
        return f"p = {eff.p_value:.4f}"

    if interaction_sig:
        p_int_disp = _format_p_statement(interaction_effect)
        warnings.append(
            f"Significant interaction effect detected between '{factor_a_column}' and '{factor_b_column}' "
            f"({p_int_disp}). "
            f"Marginal main effects may be misleading; inspect simple main effects for specific condition differences."
        )

        if options.perform_simple_effects:
            simple_effects = compute_simple_effects(
                clean_df,
                response_column,
                factor_a_column,
                factor_b_column,
                alpha=alpha,
                post_hoc_method=options.post_hoc_method,
            )
    else:
        # When interaction is not significant, evaluate marginal main effect post-hocs
        eff_a = effects.get(factor_a_column)
        if eff_a and eff_a.is_significant and len(levels_a) > 2:
            post_hoc_a = run_post_hoc(clean_df, response_column, factor_a_column, options.post_hoc_method, alpha)
            post_hoc_comparisons.extend(post_hoc_a)

        eff_b = effects.get(factor_b_column)
        if eff_b and eff_b.is_significant and len(levels_b) > 2:
            post_hoc_b = run_post_hoc(clean_df, response_column, factor_b_column, options.post_hoc_method, alpha)
            post_hoc_comparisons.extend(post_hoc_b)

    # 6. Scientific Interpretation Statement
    fa_eff = effects.get(factor_a_column)
    fb_eff = effects.get(factor_b_column)
    p_fa_str = _format_p_statement(fa_eff)
    p_fb_str = _format_p_statement(fb_eff)
    p_int_str = _format_p_statement(interaction_effect)

    statement = (
        f"Two-Way ANOVA (Type III SS) on '{response_column}' across Factor A ('{factor_a_column}', {p_fa_str}) "
        f"and Factor B ('{factor_b_column}', {p_fb_str}) revealed "
        f"{'a statistically significant' if interaction_sig else 'no statistically significant'} interaction "
        f"effect ({p_int_str}) at alpha = {alpha}."
    )

    return TwoWayAnovaResult(
        model_formula=f"{response_column} ~ C({factor_a_column}, Sum) * C({factor_b_column}, Sum)",
        response_column=response_column,
        factor_a_column=factor_a_column,
        factor_b_column=factor_b_column,
        factor_a_levels=levels_a,
        factor_b_levels=levels_b,
        cell_sample_sizes=cell_sample_sizes,
        total_rows_input=len(df),
        valid_rows_used=len(clean_df),
        excluded_rows_count=excluded_rows_count,
        exclusion_reasons=exclusion_reasons,
        design_balance=design_balance,
        is_balanced=is_balanced,
        contrast_coding="sum-to-zero (deviation)",
        anova_type="Type III",
        effects=effects,
        assumptions=assumptions,
        interaction_significant=interaction_sig,
        post_hoc_method=options.post_hoc_method.value,
        post_hoc_comparisons=post_hoc_comparisons,
        simple_effects=simple_effects,
        warnings=warnings,
        scientific_statement=statement,
    )


def run_post_hoc(
    df: pd.DataFrame,
    response_col: str,
    factor_col: str,
    method: PostHocMethod,
    alpha: float,
) -> list[PostHocResult]:
    """Helper to run pairwise post-hoc tests on a single factor."""
    if method == PostHocMethod.NONE:
        return []
    if method == PostHocMethod.TUKEY:
        return run_post_hoc_tukey(df, response_col, factor_col, alpha=alpha)
    return run_post_hoc_pairwise_ttest(df, response_col, factor_col, method=method, alpha=alpha)


def compute_simple_effects(
    clean_df: pd.DataFrame,
    response_col: str,
    factor_a_col: str,
    factor_b_col: str,
    alpha: float = 0.05,
    post_hoc_method: PostHocMethod = PostHocMethod.TUKEY,
) -> list[SimpleEffectResult]:
    """Computes simple main effects of Factor A within each level of Factor B,
    and Factor B within each level of Factor A.
    """
    simple_results: list[SimpleEffectResult] = []

    # 1. Simple main effects of Factor A at each slice of Factor B
    levels_b = sorted(clean_df[factor_b_col].unique())
    for b_lvl in levels_b:
        sub_df = clean_df[clean_df[factor_b_col] == b_lvl]
        levels_in_slice = sorted(sub_df[factor_a_col].unique())
        if len(levels_in_slice) >= 2:
            groups = [sub_df[sub_df[factor_a_col] == a][response_col].values for a in levels_in_slice]
            f_stat, p_val = stats.f_oneway(*groups)

            k = len(levels_in_slice)
            n = len(sub_df)
            df_between = k - 1
            df_within = n - k

            p_val_float = float(p_val) if not np.isnan(p_val) else None
            f_stat_float = float(f_stat) if not np.isnan(f_stat) else None
            is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

            pairwise = []
            if post_hoc_method != PostHocMethod.NONE:
                pairwise = run_post_hoc(sub_df, response_col, factor_a_col, post_hoc_method, alpha)

            simple_results.append(
                SimpleEffectResult(
                    slice_factor=factor_b_col,
                    slice_level=str(b_lvl),
                    target_factor=factor_a_col,
                    df_between=float(df_between),
                    df_within=float(df_within),
                    f_statistic=round(f_stat_float, 4) if f_stat_float is not None else None,
                    p_value=round(p_val_float, 6) if p_val_float is not None else None,
                    is_significant=is_sig,
                    pairwise_comparisons=pairwise,
                )
            )

    # 2. Simple main effects of Factor B at each slice of Factor A
    levels_a = sorted(clean_df[factor_a_col].unique())
    for a_lvl in levels_a:
        sub_df = clean_df[clean_df[factor_a_col] == a_lvl]
        levels_in_slice = sorted(sub_df[factor_b_col].unique())
        if len(levels_in_slice) >= 2:
            groups = [sub_df[sub_df[factor_b_col] == b][response_col].values for b in levels_in_slice]
            f_stat, p_val = stats.f_oneway(*groups)

            k = len(levels_in_slice)
            n = len(sub_df)
            df_between = k - 1
            df_within = n - k

            p_val_float = float(p_val) if not np.isnan(p_val) else None
            f_stat_float = float(f_stat) if not np.isnan(f_stat) else None
            is_sig = bool(p_val_float < alpha) if p_val_float is not None else False

            pairwise = []
            if post_hoc_method != PostHocMethod.NONE:
                pairwise = run_post_hoc(sub_df, response_col, factor_b_col, post_hoc_method, alpha)

            simple_results.append(
                SimpleEffectResult(
                    slice_factor=factor_a_col,
                    slice_level=str(a_lvl),
                    target_factor=factor_b_col,
                    df_between=float(df_between),
                    df_within=float(df_within),
                    f_statistic=round(f_stat_float, 4) if f_stat_float is not None else None,
                    p_value=round(p_val_float, 6) if p_val_float is not None else None,
                    is_significant=is_sig,
                    pairwise_comparisons=pairwise,
                )
            )

    return simple_results
