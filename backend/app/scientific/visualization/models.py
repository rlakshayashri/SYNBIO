from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PlotType(StrEnum):
    """Supported scientific plot types."""

    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"
    SCATTER = "scatter"
    BAR = "bar"


class AggregationType(StrEnum):
    """Supported aggregation methods for bar charts."""

    COUNT = "count"
    MEAN = "mean"
    SUM = "sum"
    MEDIAN = "median"


class VisualizationRequest(BaseModel):
    """Request payload specifying visualization plot type and target columns."""

    plot_type: PlotType
    column: str | None = None
    x_column: str | None = None
    y_column: str | None = None
    group_column: str | None = None
    category_column: str | None = None
    value_column: str | None = None
    aggregation: AggregationType = AggregationType.COUNT


class PlotTrace(BaseModel):
    """Plotly-compatible data trace payload."""

    name: str | None = None
    x: list[Any] = Field(default_factory=list)
    y: list[Any] = Field(default_factory=list)
    type: str = "scatter"
    mode: str | None = None


class PlotMetadata(BaseModel):
    """Metadata detailing observation counts and excluded missing values."""

    observations: int
    missing_excluded: int
    group_by: str | None = None
    aggregation: str | None = None


class VisualizationResult(BaseModel):
    """Structured result returned by the scientific visualization engine."""

    dataset_id: UUID | None = None
    plot_type: PlotType
    title: str
    x_axis: str
    y_axis: str
    traces: list[PlotTrace]
    metadata: PlotMetadata
