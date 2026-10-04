from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.scientific.validation.models import ValidationResult
from app.scientific.validation.validator import validate_dataframe
from app.storage.local import LocalStorageService


class ValidationService:
    """Service encapsulating validation execution and result persistence."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def run_validation(self, dataset_id: UUID) -> ValidationResult:
        """Executes scientific data quality validation on a dataset and persists the analysis record."""
        dataset = self.db.get(Dataset, dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        # Run pure scientific validation engine
        result: ValidationResult = validate_dataframe(df, dataset_id=dataset_id)

        # Persist Analysis record in PostgreSQL
        analysis = Analysis(
            dataset_id=dataset_id,
            experiment_id=dataset.experiment_id,
            analysis_type="validation",
            parameters={},
            result=result.model_dump(mode="json"),
            software_version="0.1.0",
        )
        self.db.add(analysis)
        self.db.commit()

        return result
