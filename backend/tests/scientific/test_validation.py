from pathlib import Path

import numpy as np
import pandas as pd

from app.scientific.validation import ValidationStatus, validate_dataframe

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_clean_dataset_validation() -> None:
    """Verify that a clean dataset produces PASS status with zero warnings."""
    clean_path = FIXTURES_DIR / "clean_dataset.csv"
    df = pd.read_csv(clean_path)
    original_df = df.copy()

    result = validate_dataframe(df)

    assert result.overall_status == ValidationStatus.PASS
    assert result.summary.missing_values == 0
    assert result.summary.duplicate_rows == 0
    assert result.summary.potential_outliers == 0
    assert result.summary.empty_columns == 0
    assert len(result.warnings) == 0

    # Safety Rule: Ensure input DataFrame was NOT mutated
    pd.testing.assert_frame_equal(df, original_df)


def test_problematic_dataset_validation() -> None:
    """Verify that a problematic dataset correctly identifies missing values,
    duplicates, outliers, and empty columns."""
    prob_path = FIXTURES_DIR / "problematic_dataset.csv"
    df = pd.read_csv(prob_path)
    original_df = df.copy()

    result = validate_dataframe(df)

    # 1. Overall Status should be ERROR because 'notes' is a 100% empty column
    assert result.overall_status == ValidationStatus.ERROR
    assert result.summary.empty_columns == 1
    assert "notes" in result.checks.empty_columns

    # 2. Missing values detection
    assert result.summary.missing_values >= 1
    missing_cols = [m.column for m in result.checks.missing_values]
    assert "concentration" in missing_cols

    # 3. Duplicate rows detection
    assert result.summary.duplicate_rows == 1
    assert result.checks.duplicates.duplicate_count == 1

    # 4. Outlier detection (absorbance value 999.0)
    assert result.summary.potential_outliers >= 1
    outlier_cols = [o.column for o in result.checks.outliers]
    assert "absorbance" in outlier_cols

    # 5. Warnings verification
    assert len(result.warnings) > 0

    # Safety Rule: Ensure input DataFrame was NOT mutated
    pd.testing.assert_frame_equal(df, original_df)


def test_custom_dataframe_validation_immutability() -> None:
    """Test validation directly on an in-memory DataFrame and verify strict non-mutation."""
    data = {
        "val_a": [10.0, 12.0, 11.0, 10.5, 100.0, np.nan],
        "val_b": [1, 2, 2, 4, 5, 6],
    }
    df = pd.DataFrame(data)
    df_copy = df.copy()

    result = validate_dataframe(df)

    assert result.summary.missing_values == 1
    assert result.summary.potential_outliers == 1
    pd.testing.assert_frame_equal(df, df_copy)
