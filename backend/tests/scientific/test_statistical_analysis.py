import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import ScientificValidationError
from app.scientific.statistics import (
    AnalysisCategory,
    PostHocMethod,
    StatisticalMethod,
    run_anova_analysis,
    run_correlation_analysis,
    run_nonparametric_group_comparison,
    run_two_group_comparison,
)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Fixture providing a clean synthetic dataset with 2 groups and 2 correlated measurements."""
    np.random.seed(42)
    group_a = np.random.normal(loc=10.0, scale=1.5, size=30)
    group_b = np.random.normal(loc=12.5, scale=2.0, size=30)
    group_c = np.random.normal(loc=15.0, scale=1.8, size=30)

    val_x = np.concatenate([group_a, group_b, group_c])
    val_y = val_x * 0.8 + np.random.normal(loc=0.0, scale=0.5, size=90)
    group_col = ["Control"] * 30 + ["Treatment_A"] * 30 + ["Treatment_B"] * 30

    return pd.DataFrame({"measurement_x": val_x, "measurement_y": val_y, "treatment": group_col})


def test_pearson_correlation_analysis(sample_dataframe: pd.DataFrame):
    """Verifies Pearson correlation calculation, CI, and assumption checks."""
    result = run_correlation_analysis(
        sample_dataframe,
        column_1="measurement_x",
        column_2="measurement_y",
        method=StatisticalMethod.PEARSON,
        alpha=0.05,
    )

    assert result.category == AnalysisCategory.CORRELATION
    assert result.statistic_name == "Pearson r"
    assert result.statistic_value is not None
    assert result.statistic_value > 0.8
    assert result.p_value < 0.001
    assert result.is_significant is True
    assert result.confidence_interval is not None
    assert result.confidence_interval.lower < result.statistic_value < result.confidence_interval.upper
    assert len(result.assumptions) == 2  # Normality for both columns
    assert "returned Pearson r =" in result.statement


def test_spearman_correlation_analysis(sample_dataframe: pd.DataFrame):
    """Verifies Spearman rank correlation execution."""
    result = run_correlation_analysis(
        sample_dataframe,
        column_1="measurement_x",
        column_2="measurement_y",
        method=StatisticalMethod.SPEARMAN,
        alpha=0.05,
    )

    assert result.statistic_name == "Spearman rho"
    assert result.statistic_value > 0.8
    assert result.p_value < 0.001


def test_welch_ttest_two_groups(sample_dataframe: pd.DataFrame):
    """Verifies Welch's t-test comparing Control and Treatment_A."""
    sub_df = sample_dataframe[sample_dataframe["treatment"].isin(["Control", "Treatment_A"])]

    result = run_two_group_comparison(
        sub_df,
        value_column="measurement_x",
        group_column="treatment",
        method=StatisticalMethod.WELCH_TTEST,
        alpha=0.05,
    )

    assert result.category == AnalysisCategory.TWO_GROUP
    assert result.statistic_name == "Welch t"
    assert result.p_value < 0.001
    assert result.is_significant is True
    assert result.effect_size is not None
    assert result.effect_size.name == "Cohen's d"
    assert len(result.assumptions) == 3  # Normality 1, Normality 2, Homogeneity


def test_paired_ttest(sample_dataframe: pd.DataFrame):
    """Verifies paired t-test comparing two correlated numeric columns."""
    result = run_two_group_comparison(
        sample_dataframe,
        value_column="measurement_x",
        value_column_2="measurement_y",
        method=StatisticalMethod.PAIRED_TTEST,
        alpha=0.05,
        paired=True,
    )

    assert result.statistic_name == "Paired t"
    assert result.p_value is not None
    assert result.confidence_interval is not None


def test_one_way_anova_with_tukey(sample_dataframe: pd.DataFrame):
    """Verifies One-Way ANOVA across 3 groups with Tukey HSD post-hoc comparisons."""
    result = run_anova_analysis(
        sample_dataframe,
        value_column="measurement_x",
        group_column="treatment",
        method=StatisticalMethod.ONE_WAY_ANOVA,
        alpha=0.05,
        post_hoc_method=PostHocMethod.TUKEY,
    )

    assert result.category == AnalysisCategory.ANOVA
    assert result.statistic_name == "F"
    assert result.p_value < 0.001
    assert result.is_significant is True
    assert result.effect_size.name == "Eta-squared (eta^2)"
    assert len(result.post_hoc) == 3  # 3 pairwise comparisons (Control-TrA, Control-TrB, TrA-TrB)
    assert any(ph.is_significant for ph in result.post_hoc)


def test_mann_whitney_nonparametric(sample_dataframe: pd.DataFrame):
    """Verifies Mann-Whitney U non-parametric comparison."""
    sub_df = sample_dataframe[sample_dataframe["treatment"].isin(["Control", "Treatment_A"])]

    result = run_nonparametric_group_comparison(
        sub_df,
        value_column="measurement_x",
        group_column="treatment",
        method=StatisticalMethod.MANN_WHITNEY,
        alpha=0.05,
    )

    assert result.category == AnalysisCategory.NONPARAMETRIC
    assert result.statistic_name == "U"
    assert result.p_value < 0.001
    assert result.effect_size.name == "Rank-Biserial r"


def test_kruskal_wallis_with_bonferroni(sample_dataframe: pd.DataFrame):
    """Verifies Kruskal-Wallis multi-group non-parametric comparison with Dunn-Bonferroni post-hoc."""
    result = run_nonparametric_group_comparison(
        sample_dataframe,
        value_column="measurement_x",
        group_column="treatment",
        method=StatisticalMethod.KRUSKAL_WALLIS,
        alpha=0.05,
        post_hoc_method=PostHocMethod.BONFERRONI,
    )

    assert result.statistic_name == "H"
    assert result.p_value < 0.001
    assert result.effect_size.name == "Epsilon-squared (epsilon^2)"
    assert len(result.post_hoc) == 3


def test_insufficient_sample_size_raises():
    """Verifies ScientificValidationError is raised when sample size is insufficient."""
    small_df = pd.DataFrame({"x": [10.0], "group": ["Control"]})

    with pytest.raises(ScientificValidationError):
        run_two_group_comparison(small_df, value_column="x", group_column="group", method=StatisticalMethod.WELCH_TTEST)
