from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError, SynDataXError
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.scientific.visualization.models import (
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
from app.storage.local import LocalStorageService


class VisualizationService:
    """Service encapsulating visualization plot preparation and analysis persistence."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def run_visualization(self, dataset_id: UUID, request: VisualizationRequest) -> VisualizationResult:
        """Loads dataset file, invokes appropriate plot preparation engine, and persists analysis record."""
        dataset = self.db.get(Dataset, dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        if request.plot_type == PlotType.HISTOGRAM:
            if not request.column:
                raise SynDataXError("Histogram requires 'column' parameter.")
            result = prepare_histogram(df, column=request.column, dataset_id=dataset_id)

        elif request.plot_type == PlotType.BOXPLOT:
            if not request.column:
                raise SynDataXError("Boxplot requires 'column' parameter.")
            result = prepare_boxplot(df, column=request.column, dataset_id=dataset_id)

        elif request.plot_type == PlotType.SCATTER:
            if not request.x_column or not request.y_column:
                raise SynDataXError("Scatter plot requires 'x_column' and 'y_column' parameters.")
            result = prepare_scatter(
                df,
                x_column=request.x_column,
                y_column=request.y_column,
                group_column=request.group_column,
                dataset_id=dataset_id,
            )

        elif request.plot_type == PlotType.BAR:
            if not request.category_column:
                raise SynDataXError("Bar chart requires 'category_column' parameter.")
            result = prepare_bar_chart(
                df,
                category_column=request.category_column,
                value_column=request.value_column,
                aggregation=request.aggregation.value,
                dataset_id=dataset_id,
            )

        else:
            raise SynDataXError(f"Unsupported plot type '{request.plot_type}'.")

        # Persist Analysis record in PostgreSQL
        analysis = Analysis(
            dataset_id=dataset_id,
            analysis_type=f"visualization_{request.plot_type.value}",
            parameters=request.model_dump(mode="json"),
            result=result.model_dump(mode="json"),
            software_version="0.1.0",
        )
        self.db.add(analysis)
        self.db.commit()

        return result
