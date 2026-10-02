from uuid import UUID

import pandas as pd

from app.scientific.validation.checks import (
    check_data_types,
    check_duplicate_rows,
    check_empty_columns,
    check_iqr_outliers,
    check_missing_values,
)
from app.scientific.validation.models import (
    ValidationChecks,
    ValidationResult,
    ValidationStatus,
    ValidationSummary,
)


def validate_dataframe(df: pd.DataFrame, dataset_id: UUID | None = None) -> ValidationResult:
    """Executes scientific validation checks on a pandas DataFrame.

    This function NEVER mutates the input DataFrame.
    Independent of FastAPI, HTTP, and SQLAlchemy.
    """
    row_count = len(df)
    column_count = len(df.columns)

    missing_list = check_missing_values(df)
    duplicates_info = check_duplicate_rows(df)
    dtypes_list = check_data_types(df)
    empty_cols = check_empty_columns(df)
    outliers_list = check_iqr_outliers(df)

    # Compute summary counts
    total_missing = sum(item.missing_count for item in missing_list)
    total_duplicates = duplicates_info.duplicate_count
    total_outliers = sum(item.outlier_count for item in outliers_list)
    total_empty_cols = len(empty_cols)

    summary = ValidationSummary(
        missing_values=total_missing,
        duplicate_rows=total_duplicates,
        potential_outliers=total_outliers,
        empty_columns=total_empty_cols,
    )

    checks = ValidationChecks(
        missing_values=[item for item in missing_list if item.missing_count > 0],
        duplicates=duplicates_info,
        data_types=dtypes_list,
        outliers=outliers_list,
        empty_columns=empty_cols,
    )

    warnings: list[str] = []

    # Generate human-readable warnings
    if total_empty_cols > 0:
        for col in empty_cols:
            warnings.append(f"Column '{col}' is completely empty (100% missing values).")

    for item in missing_list:
        if item.missing_count > 0:
            warnings.append(
                f"Column '{item.column}' has {item.missing_count} missing value(s) ({item.missing_percentage}%)."
            )

    if total_duplicates > 0:
        warnings.append(
            f"Dataset contains {total_duplicates} exact duplicate row(s) ({duplicates_info.duplicate_percentage}%)."
        )

    for item in outliers_list:
        warnings.append(
            f"Column '{item.column}' has {item.outlier_count} potential outlier(s) "
            f"outside bounds [{item.lower_bound}, {item.upper_bound}]."
        )

    # Determine overall status
    if total_empty_cols > 0 or row_count == 0:
        overall_status = ValidationStatus.ERROR
    elif total_missing > 0 or total_duplicates > 0 or total_outliers > 0:
        overall_status = ValidationStatus.WARNING
    else:
        overall_status = ValidationStatus.PASS

    return ValidationResult(
        dataset_id=dataset_id,
        row_count=row_count,
        column_count=column_count,
        overall_status=overall_status,
        summary=summary,
        checks=checks,
        warnings=warnings,
    )
