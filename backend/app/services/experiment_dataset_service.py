from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DatasetNotFoundError,
    ExperimentNotFoundError,
    ScientificValidationError,
)
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.services.dataset_service import DatasetService
from app.storage.local import LocalStorageService


class ExperimentDatasetService:
    """Service encapsulating experiment <-> dataset attachment, detachment, and upload delegation."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.dataset_service = DatasetService(db, storage=storage)

    def attach_dataset(self, experiment_id: UUID, dataset_id: UUID) -> Dataset:
        """Attaches an existing dataset to an experiment.

        Validates experiment and dataset exist and belong to the same project.
        """
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        dataset = self.dataset_service.get_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        if dataset.project_id != experiment.project_id:
            raise ScientificValidationError(
                f"Dataset '{dataset_id}' project '{dataset.project_id}' does not match "
                f"experiment project '{experiment.project_id}'."
            )

        dataset.experiment_id = experiment_id
        if experiment.dataset_id is None:
            experiment.dataset_id = dataset_id

        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def detach_dataset(self, experiment_id: UUID, dataset_id: UUID) -> Dataset:
        """Detaches a dataset from an experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        dataset = self.dataset_service.get_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        if dataset.experiment_id != experiment_id:
            raise ScientificValidationError(
                f"Dataset '{dataset_id}' is not attached to experiment '{experiment_id}'."
            )

        dataset.experiment_id = None
        if experiment.dataset_id == dataset_id:
            experiment.dataset_id = None

        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def list_attached_datasets(self, experiment_id: UUID) -> Sequence[Dataset]:
        """Lists all datasets attached to an experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        stmt = (
            select(Dataset)
            .where(Dataset.experiment_id == experiment_id)
            .order_by(Dataset.created_at.desc())
        )
        return self.db.scalars(stmt).all()

    def upload_and_attach(
        self,
        experiment_id: UUID,
        file_name: str,
        file_type: str,
        file_bytes: bytes,
        name: str | None = None,
    ) -> Dataset:
        """Delegates dataset ingestion/storage to DatasetService and attaches the resulting dataset."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        dataset = self.dataset_service.upload_dataset(
            project_id=experiment.project_id,
            file_name=file_name,
            file_type=file_type,
            file_bytes=file_bytes,
            name=name,
        )
        return self.attach_dataset(experiment_id, dataset.id)
