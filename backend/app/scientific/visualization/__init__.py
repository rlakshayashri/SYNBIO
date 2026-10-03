"""Scientific visualization subpackage (histogram, boxplot, scatter, bar chart)."""

from app.scientific.visualization.models import (
    AggregationType,
    PlotMetadata,
    PlotTrace,
    PlotType,
    VisualizationRequest,
    VisualizationResult,
)
from app.scientific.visualization.plots import (
    prepare_bar_chart,
    prepare_boxplot,
    prepare_histogram,
    prepare_scatter,
)

__all__ = [
    "PlotType",
    "AggregationType",
    "VisualizationRequest",
    "PlotTrace",
    "PlotMetadata",
    "VisualizationResult",
    "prepare_histogram",
    "prepare_boxplot",
    "prepare_scatter",
    "prepare_bar_chart",
]
