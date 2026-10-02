import numpy as np
import pandas as pd

from app.scientific.validation.models import (
    DataTypeCheck,
    DuplicateCheck,
    MissingValueCheck,
    OutlierCheck,
)


def check_missing_values(df: pd.DataFrame) -> list[MissingValueCheck]:
    """Calculates missing value counts and percentages for each column."""
    total_rows = len(df)
    results: list[MissingValueCheck] = []

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        pct = round((null_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
        results.append(
            MissingValueCheck(
                column=str(col),
                missing_count=null_count,
                missing_percentage=pct,
            )
        )
    return results


def check_duplicate_rows(df: pd.DataFrame) -> DuplicateCheck:
    """Detects exact duplicate rows in the DataFrame."""
    total_rows = len(df)
    dup_count = int(df.duplicated().sum())
    pct = round((dup_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
    return DuplicateCheck(duplicate_count=dup_count, duplicate_percentage=pct)


def check_data_types(df: pd.DataFrame) -> list[DataTypeCheck]:
    """Reports detected pandas data types for each column."""
    return [DataTypeCheck(column=str(col), detected_dtype=str(df[col].dtype)) for col in df.columns]


def check_empty_columns(df: pd.DataFrame) -> list[str]:
    """Identifies columns that contain 100% missing values."""
    return [str(col) for col in df.columns if df[col].isna().all()]


def check_iqr_outliers(df: pd.DataFrame) -> list[OutlierCheck]:
    """Scans numeric columns for potential outliers using the 1.5 * IQR rule."""
    results: list[OutlierCheck] = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        # If IQR is 0 (constant column), skip or upper/lower equals q1/q3
        lower_bound = float(q1 - 1.5 * iqr)
        upper_bound = float(q3 + 1.5 * iqr)

        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outlier_count = int(len(outliers))

        if outlier_count > 0:
            total_rows = len(df)
            pct = round((outlier_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
            results.append(
                OutlierCheck(
                    column=str(col),
                    outlier_count=outlier_count,
                    outlier_percentage=pct,
                    lower_bound=round(lower_bound, 4),
                    upper_bound=round(upper_bound, 4),
                )
            )

    return results
