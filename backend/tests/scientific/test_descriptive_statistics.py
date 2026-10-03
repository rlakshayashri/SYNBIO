import numpy as np
import pandas as pd

from app.scientific.statistics.descriptive import calculate_descriptive_statistics


def test_basic_numeric_column_statistics() -> None:
    """Test basic and distribution statistics calculation for standard numeric data."""
    data = {"concentration": [10.0, 20.0, 30.0, 40.0, 50.0]}
    df = pd.DataFrame(data)
    df_copy = df.copy()

    result = calculate_descriptive_statistics(df)

    assert result.row_count == 5
    assert result.numeric_column_count == 1
    assert result.non_numeric_column_count == 0
    assert len(result.statistics) == 1

    stat = result.statistics[0]
    assert stat.column == "concentration"
    assert stat.count == 5
    assert stat.missing_count == 0
    assert stat.mean == 30.0
    assert stat.median == 30.0
    assert stat.min == 10.0
    assert stat.max == 50.0
    assert stat.range == 40.0
    assert stat.q1 == 20.0
    assert stat.q3 == 40.0
    assert stat.iqr == 20.0
    assert stat.std is not None
    assert stat.variance is not None
    assert stat.cv is not None

    # Safety Rule: Ensure input DataFrame was NOT mutated
    pd.testing.assert_frame_equal(df, df_copy)


def test_non_numeric_column_skipping() -> None:
    """Verify that non-numeric columns are skipped and listed under skipped_columns."""
    data = {
        "sample_id": ["S1", "S2", "S3"],
        "absorbance": [0.45, 0.50, 0.55],
        "notes": ["ok", "ok", "flagged"],
    }
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)

    assert result.numeric_column_count == 1
    assert result.non_numeric_column_count == 2
    assert "sample_id" in result.skipped_columns
    assert "notes" in result.skipped_columns
    assert len(result.statistics) == 1
    assert result.statistics[0].column == "absorbance"


def test_missing_values_statistics() -> None:
    """Verify statistics calculation when column contains missing (NaN) values."""
    data = {"val": [10.0, np.nan, 30.0, np.nan, 50.0]}
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)
    stat = result.statistics[0]

    assert stat.count == 3
    assert stat.missing_count == 2
    assert stat.mean == 30.0
    assert stat.median == 30.0


def test_empty_dataframe() -> None:
    """Verify behavior on an empty DataFrame (0 rows)."""
    df = pd.DataFrame({"col_a": pd.Series(dtype=float)})

    result = calculate_descriptive_statistics(df)

    assert result.row_count == 0
    assert result.numeric_column_count == 1
    assert result.statistics[0].count == 0
    assert result.statistics[0].mean is None


def test_all_nan_column() -> None:
    """Verify behavior when column contains 100% NaN values."""
    data = {"all_nan": [np.nan, np.nan, np.nan]}
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)
    stat = result.statistics[0]

    assert stat.count == 0
    assert stat.missing_count == 3
    assert stat.mean is None
    assert stat.std is None
    assert stat.cv is None


def test_single_observation() -> None:
    """Verify behavior for a single observation (N=1), where sample std/var are undefined."""
    data = {"single": [42.0]}
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)
    stat = result.statistics[0]

    assert stat.count == 1
    assert stat.mean == 42.0
    assert stat.median == 42.0
    assert stat.min == 42.0
    assert stat.max == 42.0
    assert stat.std is None
    assert stat.variance is None
    assert stat.cv is None


def test_constant_column() -> None:
    """Verify constant column where std=0, variance=0, range=0, iqr=0."""
    data = {"constant": [5.0, 5.0, 5.0, 5.0]}
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)
    stat = result.statistics[0]

    assert stat.count == 4
    assert stat.mean == 5.0
    assert stat.std == 0.0
    assert stat.variance == 0.0
    assert stat.range == 0.0
    assert stat.iqr == 0.0
    assert stat.cv == 0.0


def test_zero_mean_cv_undefined() -> None:
    """Verify zero mean case where CV is undefined (None) to avoid division by zero."""
    data = {"balanced": [-10.0, 0.0, 10.0]}
    df = pd.DataFrame(data)

    result = calculate_descriptive_statistics(df)
    stat = result.statistics[0]

    assert stat.mean == 0.0
    assert stat.std is not None
    assert stat.cv is None  # CV is undefined when mean is 0
