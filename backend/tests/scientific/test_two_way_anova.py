import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics.factorial_models import FactorialAnalysisOptions
from app.scientific.statistics.models import PostHocMethod
from app.scientific.statistics.two_way_anova import (
    calculate_partial_eta_squared,
    compute_two_way_anova,
)

# --- 1. Dataset with Clear Factor A Main Effect Only ---


def test_clear_factor_a_main_effect():
    """Verify that a dataset with a strong Factor A difference correctly identifies Factor A main effect."""
    # A has huge effect: A1 mean=10, A2 mean=50; B has no effect (B1 mean=30, B2 mean=30)
    data = {
        "yield": [9.9, 10.1, 9.8, 10.2, 49.9, 50.1, 49.8, 50.2],
        "temperature": ["30C", "30C", "30C", "30C", "37C", "37C", "37C", "37C"],
        "media": ["LB", "LB", "M9", "M9", "LB", "LB", "M9", "M9"],
    }
    df = pd.DataFrame(data)

    result = compute_two_way_anova(df, "yield", "temperature", "media")

    assert result.effects["temperature"].is_significant is True
    assert result.effects["temperature"].p_value < 0.001
    assert result.effects["temperature"].partial_eta_squared > 0.95
    assert result.effects["media"].is_significant is False
    assert result.effects["temperature × media"].is_significant is False
    assert result.interaction_significant is False


# --- 2. Dataset with Clear Factor B Main Effect Only ---


def test_clear_factor_b_main_effect():
    """Verify that a dataset with a strong Factor B difference correctly identifies Factor B main effect."""
    # B has huge effect: LB mean=10, M9 mean=100; A has no effect
    data = {
        "yield": [9.9, 10.1, 99.8, 100.2, 9.8, 10.2, 99.9, 100.1],
        "temperature": ["30C", "30C", "30C", "30C", "37C", "37C", "37C", "37C"],
        "media": ["LB", "LB", "M9", "M9", "LB", "LB", "M9", "M9"],
    }
    df = pd.DataFrame(data)

    result = compute_two_way_anova(df, "yield", "temperature", "media")

    assert result.effects["media"].is_significant is True
    assert result.effects["media"].p_value < 0.001
    assert result.effects["media"].partial_eta_squared > 0.95
    assert result.effects["temperature"].is_significant is False
    assert result.effects["temperature × media"].is_significant is False


# --- 3. Dataset with Pure Interaction Effect (Crossover) ---


def test_clear_interaction_effect_triggers_simple_effects():
    """Verify that a crossover interaction is detected and triggers simple-effects analysis."""
    # A1: LB=10, M9=50; A2: LB=50, M9=10. Marginal means are identical (30 vs 30).
    data = {
        "yield": [9.9, 10.1, 49.9, 50.1, 49.8, 50.2, 9.8, 10.2],
        "strain": ["WT", "WT", "WT", "WT", "MUT", "MUT", "MUT", "MUT"],
        "condition": ["Ctrl", "Ctrl", "Stress", "Stress", "Ctrl", "Ctrl", "Stress", "Stress"],
    }
    df = pd.DataFrame(data)

    opts = FactorialAnalysisOptions(perform_simple_effects=True, post_hoc_method=PostHocMethod.TUKEY)
    result = compute_two_way_anova(df, "yield", "strain", "condition", options=opts)

    assert result.interaction_significant is True
    assert result.effects["strain × condition"].is_significant is True
    assert result.effects["strain × condition"].p_value < 0.001
    assert len(result.simple_effects) > 0

    # Verify simple effects contain slices
    slices = {(se.slice_factor, se.slice_level) for se in result.simple_effects}
    assert ("condition", "Ctrl") in slices
    assert ("condition", "Stress") in slices
    assert ("strain", "WT") in slices
    assert ("strain", "MUT") in slices


# --- 4. Null Dataset (No Effects Detectable) ---


def test_null_dataset_no_significant_effects():
    """Verify that uniform data with zero factor differences yields no significant effects."""
    # Exactly identical distributions across all 4 cells: [20.0, 22.0]
    data = {
        "response": [20.0, 22.0, 20.0, 22.0, 20.0, 22.0, 20.0, 22.0],
        "factor_a": ["A1", "A1", "A1", "A1", "A2", "A2", "A2", "A2"],
        "factor_b": ["B1", "B1", "B2", "B2", "B1", "B1", "B2", "B2"],
    }
    df = pd.DataFrame(data)

    result = compute_two_way_anova(df, "response", "factor_a", "factor_b")

    assert result.effects["factor_a"].is_significant is False
    assert result.effects["factor_a"].p_value == 1.0
    assert result.effects["factor_a"].partial_eta_squared == 0.0
    assert result.effects["factor_b"].is_significant is False
    assert result.effects["factor_b"].p_value == 1.0
    assert result.effects["factor_b"].partial_eta_squared == 0.0
    assert result.effects["factor_a × factor_b"].is_significant is False
    assert result.effects["factor_a × factor_b"].p_value == 1.0
    assert result.effects["factor_a × factor_b"].partial_eta_squared == 0.0
    assert result.interaction_significant is False


# --- 5. Balanced Factorial Design ---


def test_balanced_factorial_design():
    """Verify design balance detection when all cells have equal sample size."""
    data = {
        "val": [1, 2, 3, 4, 5, 6, 7, 8],
        "fa": ["A1", "A1", "A2", "A2", "A1", "A1", "A2", "A2"],
        "fb": ["B1", "B1", "B1", "B1", "B2", "B2", "B2", "B2"],
    }
    df = pd.DataFrame(data)
    result = compute_two_way_anova(df, "val", "fa", "fb")

    assert result.is_balanced is True
    assert result.design_balance == "balanced"
    assert all(count == 2 for count in result.cell_sample_sizes.values())


# --- 6. Unbalanced but Estimable Design ---


def test_unbalanced_estimable_design():
    """Verify Type III ANOVA computes unconfounded effects on unbalanced but estimable designs."""
    # Cell sample counts: (2, 3, 2, 4) -> total N = 11
    data = {
        "val": [10.0, 11.0, 10.5, 11.2, 10.8, 30.0, 31.0, 30.5, 31.2, 30.8, 31.5],
        "fa": ["A1", "A1", "A1", "A1", "A1", "A2", "A2", "A2", "A2", "A2", "A2"],
        "fb": ["B1", "B1", "B2", "B2", "B2", "B1", "B1", "B2", "B2", "B2", "B2"],
    }
    df = pd.DataFrame(data)
    result = compute_two_way_anova(df, "val", "fa", "fb")

    assert result.is_balanced is False
    assert result.design_balance == "unbalanced_estimable"
    assert result.effects["fa"].is_significant is True
    assert any("Unbalanced design detected" in w for w in result.warnings)


# --- 7. Incomplete Factorial Design (Empty Cell) ---


def test_empty_cell_raises_scientific_validation_error():
    """Verify that missing combinations raise ScientificValidationError detailing empty cells."""
    # A2 x B2 has 0 observations
    data = {
        "val": [10, 12, 14, 16, 20, 22],
        "fa": ["A1", "A1", "A2", "A2", "A1", "A1"],
        "fb": ["B1", "B1", "B1", "B1", "B2", "B2"],
    }
    df = pd.DataFrame(data)

    with pytest.raises(ScientificValidationError, match="Factorial design is incomplete"):
        compute_two_way_anova(df, "val", "fa", "fb")


# --- 8. Singular Design (Insufficient Levels) ---


def test_factor_with_single_level_raises_error():
    """Verify that a factor with only 1 level raises ScientificValidationError."""
    data = {
        "val": [10, 12, 14, 16],
        "fa": ["A1", "A1", "A1", "A1"],
        "fb": ["B1", "B2", "B1", "B2"],
    }
    df = pd.DataFrame(data)

    with pytest.raises(ScientificValidationError, match="requires at least 2 distinct observed levels"):
        compute_two_way_anova(df, "val", "fa", "fb")


# --- 9. Missing and Non-Finite Value Accounting ---


def test_missing_and_non_finite_values_exclusion_policy():
    """Verify explicit accounting of NaN, infinite, and empty string exclusions."""
    data = {
        "val": [10.0, np.nan, np.inf, -np.inf, 12.0, 20.0, 22.0, 30.0, 32.0, 40.0],
        "fa": ["A1", "A1", "A1", "A1", "", "A1", "A1", "A2", "A2", "A2"],
        "fb": ["B1", "B1", "B1", "B1", "B1", None, "B1", "B2", "B2", "B2"],
    }
    df = pd.DataFrame(data)

    # Add extra rows to ensure remaining clean rows satisfy minimum sample size
    extra = pd.DataFrame({
        "val": [11.0, 13.0, 29.0, 31.0],
        "fa": ["A1", "A1", "A2", "A2"],
        "fb": ["B2", "B2", "B1", "B1"],
    })
    full_df = pd.concat([df, extra], ignore_index=True)

    result = compute_two_way_anova(full_df, "val", "fa", "fb")

    assert result.total_rows_input == 14
    assert result.excluded_rows_count > 0
    assert result.exclusion_reasons["missing_or_non_numeric_response"] >= 1
    assert result.exclusion_reasons["infinite_response"] >= 2
    assert any("Excluded" in w for w in result.warnings)


# --- 10. Invalid Column Selections ---


def test_invalid_column_selections():
    """Verify validation errors for missing or duplicate column specifications."""
    df = pd.DataFrame({"y": [1, 2, 3, 4], "a": ["A1", "A1", "A2", "A2"], "b": ["B1", "B2", "B1", "B2"]})

    with pytest.raises(ScientificValidationError, match="Response column 'nonexistent'"):
        compute_two_way_anova(df, "nonexistent", "a", "b")

    with pytest.raises(ScientificValidationError, match="cannot be the identical column"):
        compute_two_way_anova(df, "y", "a", "a")


# --- 11. Non-Numeric Response Values ---


def test_non_numeric_response_column():
    """Verify that non-numeric response columns fail validation."""
    df = pd.DataFrame({
        "response": ["text1", "text2", "text3", "text4"],
        "fa": ["A1", "A1", "A2", "A2"],
        "fb": ["B1", "B2", "B1", "B2"],
    })
    with pytest.raises(ScientificValidationError, match="Insufficient valid observations"):
        compute_two_way_anova(df, "response", "fa", "fb")


# --- 12. Insufficient Residual Degrees of Freedom ---


def test_insufficient_residual_degrees_of_freedom():
    """Verify rejection when N equals cell parameter count (0 degrees of freedom for error)."""
    # 4 observations for 4 cells -> df_residual = 0
    df = pd.DataFrame({
        "val": [10.0, 15.0, 20.0, 25.0],
        "fa": ["A1", "A1", "A2", "A2"],
        "fb": ["B1", "B2", "B1", "B2"],
    })
    with pytest.raises(ScientificValidationError, match="Insufficient residual degrees of freedom"):
        compute_two_way_anova(df, "val", "fa", "fb")


# --- 13. Type III Configuration and Sum-to-Zero Contrasts ---


def test_type_iii_and_sum_contrasts_metadata():
    """Verify that model formula and metadata record sum-to-zero contrasts and Type III SS."""
    df = pd.DataFrame({
        "yield": [10, 12, 14, 16, 20, 22, 28, 30],
        "fa": ["A1", "A1", "A2", "A2", "A1", "A1", "A2", "A2"],
        "fb": ["B1", "B1", "B1", "B1", "B2", "B2", "B2", "B2"],
    })
    result = compute_two_way_anova(df, "yield", "fa", "fb")

    assert result.contrast_coding == "sum-to-zero (deviation)"
    assert result.anova_type == "Type III"
    assert "C(fa, Sum)" in result.model_formula
    assert "C(fb, Sum)" in result.model_formula


# --- 14. Partial Eta-Squared Analytical Calculation ---


def test_partial_eta_squared_analytical_accuracy():
    """Verify partial eta-squared and CI against independent analytical formulation."""
    ss_eff = 72.0
    ss_err = 8.0
    df_eff = 1.0
    df_err = 4.0

    eta_p, ci, interp = calculate_partial_eta_squared(ss_eff, ss_err, df_eff, df_err, confidence_level=0.95)

    expected_eta_p = round(72.0 / (72.0 + 8.0), 4)  # 0.9000
    assert eta_p == expected_eta_p
    assert interp == "large"
    assert ci is not None
    assert len(ci) == 2
    assert ci[0] < eta_p < ci[1]


# --- 15. Assumption Diagnostics Execution ---


def test_assumption_diagnostics_structure():
    """Verify that normality, homogeneity, and influence diagnostics are evaluated and reported."""
    df = pd.DataFrame({
        "val": [10, 12, 14, 16, 20, 22, 28, 30],
        "fa": ["A1", "A1", "A2", "A2", "A1", "A1", "A2", "A2"],
        "fb": ["B1", "B1", "B1", "B1", "B2", "B2", "B2", "B2"],
    })
    result = compute_two_way_anova(df, "val", "fa", "fb")

    assumption_names = [a.name for a in result.assumptions]
    assert any("Normality" in name for name in assumption_names)
    assert any("Homogeneity" in name for name in assumption_names)
    assert any("Cook's Distance" in name for name in assumption_names)


# --- 16. Multiple Comparison Post-Hoc Adjustments ---


def test_post_hoc_adjustments_tukey_and_bonferroni():
    """Verify that multiple comparison adjustments execute and produce structured comparisons."""
    # 3 levels of factor_a, 2 levels of factor_b
    data = {
        "val": [10.0, 10.5, 20.0, 20.5, 30.0, 30.5, 11.0, 11.5, 21.0, 21.5, 31.0, 31.5],
        "fa": ["Low", "Low", "Med", "Med", "High", "High", "Low", "Low", "Med", "Med", "High", "High"],
        "fb": ["Ctrl", "Ctrl", "Ctrl", "Ctrl", "Ctrl", "Ctrl", "Trt", "Trt", "Trt", "Trt", "Trt", "Trt"],
    }
    df = pd.DataFrame(data)

    # Tukey
    opts_tukey = FactorialAnalysisOptions(post_hoc_method=PostHocMethod.TUKEY)
    res_tukey = compute_two_way_anova(df, "val", "fa", "fb", options=opts_tukey)
    assert len(res_tukey.post_hoc_comparisons) > 0
    assert any(c.correction_method == "Tukey HSD" for c in res_tukey.post_hoc_comparisons)

    # Bonferroni
    opts_bonf = FactorialAnalysisOptions(post_hoc_method=PostHocMethod.BONFERRONI)
    res_bonf = compute_two_way_anova(df, "val", "fa", "fb", options=opts_bonf)
    assert len(res_bonf.post_hoc_comparisons) > 0


# --- 17. Simple Effects Follow-Up Structure ---


def test_simple_effects_pairwise_breakdown():
    """Verify that simple effects contain slice levels, F-tests, and pairwise comparisons."""
    data = {
        "val": [10.0, 11.0, 40.0, 41.0, 50.0, 51.0, 12.0, 13.0],
        "gene": ["Cas9", "Cas9", "Cas9", "Cas9", "dCas9", "dCas9", "dCas9", "dCas9"],
        "temp": ["30C", "30C", "37C", "37C", "30C", "30C", "37C", "37C"],
    }
    df = pd.DataFrame(data)

    res = compute_two_way_anova(df, "val", "gene", "temp")
    assert res.interaction_significant is True
    assert len(res.simple_effects) == 4
    for se in res.simple_effects:
        assert se.slice_factor in ["gene", "temp"]
        assert se.df_between is not None
        assert se.df_within is not None


# --- 18. Stable Serialization of Results and Statements ---


def test_serialization_and_statement():
    """Verify clean Pydantic serialization without numpy/NaN serialization failures."""
    df = pd.DataFrame({
        "val": [10, 12, 14, 16, 20, 22, 28, 30],
        "fa": ["A1", "A1", "A2", "A2", "A1", "A1", "A2", "A2"],
        "fb": ["B1", "B1", "B1", "B1", "B2", "B2", "B2", "B2"],
    })
    result = compute_two_way_anova(df, "val", "fa", "fb")

    # Verify dict and json serialization
    dumped_dict = result.model_dump()
    assert isinstance(dumped_dict, dict)
    assert dumped_dict["test_name"] == "Two-Way ANOVA (Type III SS)"

    dumped_json = result.model_dump_json()
    assert isinstance(dumped_json, str)
    assert "Two-Way ANOVA (Type III SS)" in dumped_json
    assert len(result.scientific_statement) > 20
