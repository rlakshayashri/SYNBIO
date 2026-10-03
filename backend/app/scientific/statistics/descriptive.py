import math
from uuid import UUID

import numpy as np
import pandas as pd

from app.scientific.statistics.models import ColumnStatistics, DescriptiveStatisticsResult


def _clean_float(val: float | None) -> float | None:
    """Utility helper to round floats and ensure NaN/Inf values become None."""
    if val is None or math.isnan(val) or math.isinf(val):
        return None
    return round(float(val), 6)


def calculate_descriptive_statistics(df: pd.DataFrame, dataset_id: UUID | None = None) -> DescriptiveStatisticsResult:
    """Calculates descriptive statistics for all numeric columns in a pandas DataFrame.

    Handles edge cases (empty dataset, all-NaN columns, single observations, zero mean)
    and strictly preserves input DataFrame immutability.
    """
    row_count = len(df)

    # Separate numeric columns from categorical/text columns
    numeric_col_names = list(df.select_dtypes(include=[np.number]).columns)
    non_numeric_col_names = [str(col) for col in df.columns if col not in numeric_col_names]

    stats_list: list[ColumnStatistics] = []

    for col in numeric_col_names:
        col_str = str(col)
        total_missing = int(df[col].isna().sum())
        valid_series = df[col].dropna()
        valid_count = int(len(valid_series))

        if valid_count == 0:
            # Column contains only NaN or zero valid numeric observations
            stats_list.append(
                ColumnStatistics(
                    column=col_str,
                    count=0,
                    missing_count=total_missing,
                )
            )
            continue

        mean_val = float(valid_series.mean())
        median_val = float(valid_series.median())
        min_val = float(valid_series.min())
        max_val = float(valid_series.max())
        range_val = float(max_val - min_val)

        q1_val = float(valid_series.quantile(0.25))
        q2_val = median_val
        q3_val = float(valid_series.quantile(0.75))
        iqr_val = float(q3_val - q1_val)

        # Standard deviation and variance require N >= 2
        if valid_count >= 2:
            std_val = float(valid_series.std(ddof=1))
            variance_val = float(valid_series.var(ddof=1))
        else:
            std_val = None
            variance_val = None

        # Coefficient of variation (CV) = std / mean (only if mean is non-zero)
        if std_val is not None and abs(mean_val) > 1e-12:
            cv_val = std_val / mean_val
        else:
            cv_val = None

        stats_list.append(
            ColumnStatistics(
                column=col_str,
                count=valid_count,
                missing_count=total_missing,
                mean=_clean_float(mean_val),
                median=_clean_float(median_val),
                std=_clean_float(std_val),
                variance=_clean_float(variance_val),
                min=_clean_float(min_val),
                max=_clean_float(max_val),
                q1=_clean_float(q1_val),
                q2=_clean_float(q2_val),
                q3=_clean_float(q3_val),
                iqr=_clean_float(iqr_val),
                range=_clean_float(range_val),
                cv=_clean_float(cv_val),
            )
        )

    return DescriptiveStatisticsResult(
        dataset_id=dataset_id,
        row_count=row_count,
        numeric_column_count=len(numeric_col_names),
        non_numeric_column_count=len(non_numeric_col_names),
        statistics=stats_list,
        skipped_columns=non_numeric_col_names,
    )
