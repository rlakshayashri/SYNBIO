import pandas as pd
import pytest

from app.core.exceptions import SynDataXError
from app.scientific.visualization.models import PlotType
from app.scientific.visualization.plots import (
    prepare_bar_chart,
    prepare_boxplot,
    prepare_histogram,
    prepare_scatter,
)


def test_histogram_generation() -> None:
    """Verify histogram calculation and null filtering."""
    df = pd.DataFrame({"absorbance": [0.45, 0.50, None, 0.60, 0.70]})
    df_copy = df.copy()

    res = prepare_histogram(df, column="absorbance")

    assert res.plot_type == PlotType.HISTOGRAM
    assert res.title == "Distribution of absorbance"
    assert res.x_axis == "absorbance"
    assert res.y_axis == "Frequency"
    assert len(res.traces) == 1
    assert res.traces[0].x == [0.45, 0.5, 0.6, 0.7]
    assert res.metadata.observations == 4
    assert res.metadata.missing_excluded == 1

    # Safety Rule: Ensure input DataFrame was NOT mutated
    pd.testing.assert_frame_equal(df, df_copy)


def test_boxplot_generation() -> None:
    """Verify boxplot plot trace preparation."""
    df = pd.DataFrame({"concentration": [10.0, 20.0, 30.0, 40.0, 100.0]})
    df_copy = df.copy()

    res = prepare_boxplot(df, column="concentration")

    assert res.plot_type == PlotType.BOXPLOT
    assert res.traces[0].type == "box"
    assert res.traces[0].y == [10.0, 20.0, 30.0, 40.0, 100.0]
    assert res.metadata.observations == 5

    pd.testing.assert_frame_equal(df, df_copy)


def test_scatter_without_grouping() -> None:
    """Verify scatter plot trace generation for two numeric columns."""
    df = pd.DataFrame(
        {
            "concentration": [1.0, 2.0, 3.0, None],
            "absorbance": [0.2, 0.4, 0.6, 0.8],
        }
    )

    res = prepare_scatter(df, x_column="concentration", y_column="absorbance")

    assert res.plot_type == PlotType.SCATTER
    assert len(res.traces) == 1
    assert res.traces[0].x == [1.0, 2.0, 3.0]
    assert res.traces[0].y == [0.2, 0.4, 0.6]
    assert res.metadata.observations == 3
    assert res.metadata.missing_excluded == 1


def test_scatter_with_categorical_grouping() -> None:
    """Verify scatter plot trace grouping when group_column is specified."""
    df = pd.DataFrame(
        {
            "concentration": [1.0, 2.0, 3.0, 4.0],
            "absorbance": [0.2, 0.4, 0.6, 0.8],
            "treatment": ["Ctrl", "Ctrl", "TrtA", "TrtA"],
        }
    )

    res = prepare_scatter(df, x_column="concentration", y_column="absorbance", group_column="treatment")

    assert res.plot_type == PlotType.SCATTER
    assert len(res.traces) == 2
    trace_names = [t.name for t in res.traces]
    assert "Ctrl" in trace_names
    assert "TrtA" in trace_names
    assert res.metadata.group_by == "treatment"


def test_bar_chart_count_mode() -> None:
    """Verify bar chart observation count by category."""
    df = pd.DataFrame({"condition": ["Control", "Control", "Treatment", "Control"]})

    res = prepare_bar_chart(df, category_column="condition")

    assert res.plot_type == PlotType.BAR
    assert res.traces[0].x == ["Control", "Treatment"]
    assert res.traces[0].y == [3, 1]


def test_bar_chart_aggregation_mode() -> None:
    """Verify bar chart mean value aggregation by category."""
    df = pd.DataFrame(
        {
            "condition": ["Control", "Control", "Treatment", "Treatment"],
            "absorbance": [0.2, 0.4, 0.8, 1.0],
        }
    )

    res = prepare_bar_chart(df, category_column="condition", value_column="absorbance", aggregation="mean")

    assert res.plot_type == PlotType.BAR
    assert res.traces[0].x == ["Control", "Treatment"]
    assert res.traces[0].y == [0.3, 0.9]


def test_invalid_column_raises_syndatax_error() -> None:
    df = pd.DataFrame({"col_a": [1, 2, 3]})
    with pytest.raises(SynDataXError):
        prepare_histogram(df, column="missing_col")
