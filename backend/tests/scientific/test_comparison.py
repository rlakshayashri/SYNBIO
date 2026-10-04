import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import ScientificValidationError
from app.scientific.comparison.engine import execute_experimental_comparison
from app.scientific.statistics.models import (
    PostHocMethod,
    StatisticalMethod,
)


def test_execute_experimental_comparison_two_group():
    df = pd.DataFrame({
        "group": ["CTRL", "CTRL", "CTRL", "TRT", "TRT", "TRT"],
        "expression": [10.2, 11.1, 10.8, 18.5, 19.2, 18.8],
    })
    df_orig = df.copy()

    result = execute_experimental_comparison(
        df=df,
        measurement_column="expression",
        comparison_type="two_group",
        group_column="group",
        group_a_code="CTRL",
        group_b_code="TRT",
        method=StatisticalMethod.WELCH_TTEST,
        alpha=0.05,
    )

    # Immutability check
    pd.testing.assert_frame_equal(df, df_orig)

    assert "group_summaries" in result
    assert "statistical_result" in result
    assert len(result["group_summaries"]) == 2

    stat_res = result["statistical_result"]
    assert stat_res.p_value is not None
    assert stat_res.p_value < 0.05
    assert stat_res.is_significant is True


def test_execute_experimental_comparison_anova():
    df = pd.DataFrame({
        "condition": ["G1", "G1", "G1", "G2", "G2", "G2", "G3", "G3", "G3"],
        "yield": [5.1, 5.3, 5.0, 8.2, 8.5, 8.1, 12.0, 12.4, 12.1],
    })

    result = execute_experimental_comparison(
        df=df,
        measurement_column="yield",
        comparison_type="anova",
        group_column="condition",
        method=StatisticalMethod.ONE_WAY_ANOVA,
        alpha=0.05,
        post_hoc_method=PostHocMethod.TUKEY,
    )

    assert len(result["group_summaries"]) == 3
    stat_res = result["statistical_result"]
    assert stat_res.p_value is not None
    assert stat_res.p_value < 0.001
    assert len(stat_res.post_hoc) > 0


def test_execute_experimental_comparison_nonparametric():
    df = pd.DataFrame({
        "dosage": ["LOW", "LOW", "LOW", "HIGH", "HIGH", "HIGH"],
        "response": [1.2, 1.5, 1.1, 9.8, 10.2, 9.5],
    })

    result = execute_experimental_comparison(
        df=df,
        measurement_column="response",
        comparison_type="nonparametric",
        group_column="dosage",
        method=StatisticalMethod.MANN_WHITNEY,
        alpha=0.05,
    )

    stat_res = result["statistical_result"]
    assert stat_res.statistic_name == "U"
    assert stat_res.p_value is not None


def test_execute_experimental_comparison_missing_values():
    df = pd.DataFrame({
        "group": ["A", "A", "A", "B", "B", "B"],
        "val": [1.0, np.nan, 3.0, 10.0, 12.0, np.nan],
    })

    result = execute_experimental_comparison(
        df=df,
        measurement_column="val",
        comparison_type="two_group",
        group_column="group",
    )

    summaries = {g.group_name: g for g in result["group_summaries"]}
    assert summaries["A"].sample_size_total == 3
    assert summaries["A"].sample_size_valid == 2
    assert summaries["A"].missing_count == 1


def test_invalid_column_raises_error():
    df = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ScientificValidationError):
        execute_experimental_comparison(
            df=df,
            measurement_column="nonexistent",
        )
