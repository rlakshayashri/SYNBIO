import math
from uuid import UUID

import numpy as np
import pandas as pd

from app.core.exceptions import SynDataXError
from app.scientific.visualization.models import (
    PlotMetadata,
    PlotTrace,
    PlotType,
    VisualizationResult,
)


def _clean_list(vals: list) -> list:
    """Helper converting pandas/numpy values to JSON-serializable Python native types."""
    clean: list = []
    for v in vals:
        if pd.isna(v) or v is None:
            clean.append(None)
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            clean.append(None)
        elif isinstance(v, (np.integer, np.int64)):
            clean.append(int(v))
        elif isinstance(v, (np.floating, np.float64)):
            clean.append(round(float(v), 4))
        else:
            clean.append(str(v) if not isinstance(v, (str, int, float, bool)) else v)
    return clean


def prepare_histogram(df: pd.DataFrame, column: str, dataset_id: UUID | None = None) -> VisualizationResult:
    """Prepares scientific histogram data for a numeric column.

    Strictly preserves input DataFrame immutability.
    """
    if column not in df.columns:
        raise SynDataXError(f"Column '{column}' does not exist in dataset.")

    total_rows = len(df)
    series = df[column].dropna()
    clean_vals = _clean_list(series.tolist())
    obs_count = len(clean_vals)
    missing_count = total_rows - obs_count

    trace = PlotTrace(
        name=column,
        x=clean_vals,
        type="histogram",
    )

    return VisualizationResult(
        dataset_id=dataset_id,
        plot_type=PlotType.HISTOGRAM,
        title=f"Distribution of {column}",
        x_axis=column,
        y_axis="Frequency",
        traces=[trace],
        metadata=PlotMetadata(
            observations=obs_count,
            missing_excluded=missing_count,
        ),
    )


def prepare_boxplot(df: pd.DataFrame, column: str, dataset_id: UUID | None = None) -> VisualizationResult:
    """Prepares scientific box plot data for a numeric column."""
    if column not in df.columns:
        raise SynDataXError(f"Column '{column}' does not exist in dataset.")

    total_rows = len(df)
    series = df[column].dropna()
    clean_vals = _clean_list(series.tolist())
    obs_count = len(clean_vals)
    missing_count = total_rows - obs_count

    trace = PlotTrace(
        name=column,
        y=clean_vals,
        type="box",
    )

    return VisualizationResult(
        dataset_id=dataset_id,
        plot_type=PlotType.BOXPLOT,
        title=f"Spread and Potential Outliers of {column}",
        x_axis=column,
        y_axis="Observed Value",
        traces=[trace],
        metadata=PlotMetadata(
            observations=obs_count,
            missing_excluded=missing_count,
        ),
    )


def prepare_scatter(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    group_column: str | None = None,
    dataset_id: UUID | None = None,
) -> VisualizationResult:
    """Prepares scientific scatter plot data for X and Y numeric columns, with optional categorical grouping."""
    if x_column not in df.columns:
        raise SynDataXError(f"X-axis column '{x_column}' does not exist in dataset.")
    if y_column not in df.columns:
        raise SynDataXError(f"Y-axis column '{y_column}' does not exist in dataset.")

    cols_to_select = [x_column, y_column]
    has_grouping = group_column is not None and group_column in df.columns
    if has_grouping:
        cols_to_select.append(group_column)

    subset = df[cols_to_select].dropna(subset=[x_column, y_column])
    total_rows = len(df)
    obs_count = len(subset)
    missing_count = total_rows - obs_count

    traces: list[PlotTrace] = []

    if has_grouping:
        for group_val, group_df in subset.groupby(group_column):
            x_vals = _clean_list(group_df[x_column].tolist())
            y_vals = _clean_list(group_df[y_column].tolist())
            traces.append(
                PlotTrace(
                    name=str(group_val),
                    x=x_vals,
                    y=y_vals,
                    type="scatter",
                    mode="markers",
                )
            )
    else:
        x_vals = _clean_list(subset[x_column].tolist())
        y_vals = _clean_list(subset[y_column].tolist())
        traces.append(
            PlotTrace(
                name="Observations",
                x=x_vals,
                y=y_vals,
                type="scatter",
                mode="markers",
            )
        )

    title = f"{y_column} vs {x_column}"
    if has_grouping:
        title += f" (Grouped by {group_column})"

    return VisualizationResult(
        dataset_id=dataset_id,
        plot_type=PlotType.SCATTER,
        title=title,
        x_axis=x_column,
        y_axis=y_column,
        traces=traces,
        metadata=PlotMetadata(
            observations=obs_count,
            missing_excluded=missing_count,
            group_by=group_column if has_grouping else None,
        ),
    )


def prepare_bar_chart(
    df: pd.DataFrame,
    category_column: str,
    value_column: str | None = None,
    aggregation: str = "count",
    dataset_id: UUID | None = None,
) -> VisualizationResult:
    """Prepares scientific bar chart data with categorical counts or numeric aggregations."""
    if category_column not in df.columns:
        raise SynDataXError(f"Category column '{category_column}' does not exist in dataset.")

    total_rows = len(df)
    agg_clean = aggregation.lower()

    if value_column and value_column in df.columns:
        subset = df[[category_column, value_column]].dropna()
        obs_count = len(subset)
        missing_count = total_rows - obs_count

        if agg_clean == "mean":
            grouped = subset.groupby(category_column)[value_column].mean()
        elif agg_clean == "sum":
            grouped = subset.groupby(category_column)[value_column].sum()
        elif agg_clean == "median":
            grouped = subset.groupby(category_column)[value_column].median()
        else:
            grouped = subset.groupby(category_column)[value_column].count()

        cat_names = _clean_list(list(grouped.index.astype(str)))
        agg_values = _clean_list(list(grouped.values))
        y_axis_label = f"{agg_clean.capitalize()} of {value_column}"
        title = f"{agg_clean.capitalize()} {value_column} by {category_column}"
    else:
        series = df[category_column].dropna()
        obs_count = len(series)
        missing_count = total_rows - obs_count

        counts = series.value_counts()
        cat_names = _clean_list(list(counts.index.astype(str)))
        agg_values = _clean_list(list(counts.values))
        y_axis_label = "Observation Count"
        title = f"Count of Observations by {category_column}"

    trace = PlotTrace(
        name=category_column,
        x=cat_names,
        y=agg_values,
        type="bar",
    )

    return VisualizationResult(
        dataset_id=dataset_id,
        plot_type=PlotType.BAR,
        title=title,
        x_axis=category_column,
        y_axis=y_axis_label,
        traces=[trace],
        metadata=PlotMetadata(
            observations=obs_count,
            missing_excluded=missing_count,
            aggregation=agg_clean if value_column else "count",
        ),
    )
