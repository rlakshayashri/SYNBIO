from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    DatasetNotFoundError,
    ProjectNotFoundError,
)
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.models.project import Project
from app.models.replicate import Replicate
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate
from app.services.dataset_service import DatasetService


class ExperimentService:
    """Service encapsulating database logic for Experiment lifecycle management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        """Retrieves an Experiment by ID with groups, replicates, and comparisons loaded."""
        stmt = (
            select(Experiment)
            .options(
                joinedload(Experiment.groups).joinedload(ExperimentalGroup.replicates),
                joinedload(Experiment.comparisons),
            )
            .where(Experiment.id == experiment_id)
        )
        return self.db.scalar(stmt)

    def list_all(
        self, project_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> Sequence[Experiment]:
        """Lists experiments with optional project filtering and pagination."""
        stmt = (
            select(Experiment)
            .options(
                joinedload(Experiment.groups).joinedload(ExperimentalGroup.replicates),
                joinedload(Experiment.comparisons),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Experiment.created_at.desc())
        )
        if project_id:
            stmt = stmt.where(Experiment.project_id == project_id)

        return self.db.scalars(stmt).unique().all()

    def create(self, schema: ExperimentCreate) -> Experiment:
        """Creates a new Experiment container with optional initial groups and replicates."""
        project = self.db.scalar(select(Project).where(Project.id == schema.project_id))
        if not project:
            raise ProjectNotFoundError(f"Project with ID '{schema.project_id}' not found.")

        if schema.dataset_id:
            dataset_service = DatasetService(self.db)
            if not dataset_service.get_by_id(schema.dataset_id):
                raise DatasetNotFoundError(f"Dataset with ID '{schema.dataset_id}' not found.")

        experiment = Experiment(
            project_id=schema.project_id,
            dataset_id=schema.dataset_id,
            name=schema.name,
            description=schema.description,
            status=schema.status,
            objective=schema.objective,
            organism=schema.organism,
            condition_type=schema.condition_type,
            notes=schema.notes,
        )
        self.db.add(experiment)
        self.db.flush()

        # Add initial groups & replicates if provided in creation payload
        for g_schema in schema.groups:
            group = ExperimentalGroup(
                experiment_id=experiment.id,
                name=g_schema.name,
                group_code=g_schema.group_code,
                is_control=g_schema.is_control,
                description=g_schema.description,
                metadata_payload=g_schema.metadata_payload,
            )
            self.db.add(group)
            self.db.flush()

            for r_schema in g_schema.replicates:
                replicate = Replicate(
                    group_id=group.id,
                    replicate_name=r_schema.replicate_name,
                    sample_identifier=r_schema.sample_identifier,
                    row_index=r_schema.row_index,
                    replicate_type=r_schema.replicate_type,
                    metadata_payload=r_schema.metadata_payload,
                )
                self.db.add(replicate)

        self.db.commit()
        return self.get_by_id(experiment.id)  # type: ignore[return-value]

    def update(self, experiment_id: UUID, schema: ExperimentUpdate) -> Experiment | None:
        """Updates an existing Experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            return None

        if schema.dataset_id is not None:
            dataset_service = DatasetService(self.db)
            if not dataset_service.get_by_id(schema.dataset_id):
                raise DatasetNotFoundError(f"Dataset with ID '{schema.dataset_id}' not found.")

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(experiment, key, value)

        self.db.commit()
        return self.get_by_id(experiment_id)

    def delete(self, experiment_id: UUID) -> bool:
        """Deletes an Experiment by ID."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            return False
        self.db.delete(experiment)
        self.db.commit()
        return True
