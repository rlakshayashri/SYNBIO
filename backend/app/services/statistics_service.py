from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.scientific.statistics.descriptive import calculate_descriptive_statistics
from app.scientific.statistics.models import DescriptiveStatisticsResult
from app.storage.local import LocalStorageService


class StatisticsService:
    """Service encapsulating descriptive statistics execution and analysis persistence."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def run_descriptive_statistics(self, dataset_id: UUID) -> DescriptiveStatisticsResult:
        """Executes descriptive statistics calculation on a dataset and persists the analysis record."""
        dataset = self.db.get(Dataset, dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        # Run pure scientific statistics engine
        result: DescriptiveStatisticsResult = calculate_descriptive_statistics(df, dataset_id=dataset_id)

        # Persist Analysis record in PostgreSQL
        analysis = Analysis(
            dataset_id=dataset_id,
            analysis_type="descriptive_statistics",
            parameters={},
            result=result.model_dump(mode="json"),
            software_version="0.1.0",
        )
        self.db.add(analysis)
        self.db.commit()

        return result
