from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.models.replicate import Replicate
from app.schemas.experimental_group import ExperimentalGroupCreate, ExperimentalGroupUpdate


class GroupService:
    """Service encapsulating database logic for ExperimentalGroup lifecycle management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, group_id: UUID) -> ExperimentalGroup | None:
        """Retrieves an ExperimentalGroup by ID with replicates loaded."""
        stmt = (
            select(ExperimentalGroup)
            .options(joinedload(ExperimentalGroup.replicates))
            .where(ExperimentalGroup.id == group_id)
        )
        return self.db.scalar(stmt)

    def list_for_experiment(self, experiment_id: UUID) -> Sequence[ExperimentalGroup]:
        """Lists all experimental groups for a specific experiment."""
        stmt = (
            select(ExperimentalGroup)
            .options(joinedload(ExperimentalGroup.replicates))
            .where(ExperimentalGroup.experiment_id == experiment_id)
            .order_by(ExperimentalGroup.created_at.asc())
        )
        return self.db.scalars(stmt).unique().all()

    def create(self, experiment_id: UUID, schema: ExperimentalGroupCreate) -> ExperimentalGroup:
        """Adds a new ExperimentalGroup to an existing Experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        group = ExperimentalGroup(
            experiment_id=experiment_id,
            name=schema.name,
            group_code=schema.group_code,
            is_control=schema.is_control,
            description=schema.description,
            metadata_payload=schema.metadata_payload,
        )
        self.db.add(group)
        self.db.flush()

        for r_schema in schema.replicates:
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
        return self.get_by_id(group.id)  # type: ignore[return-value]

    def update(self, group_id: UUID, schema: ExperimentalGroupUpdate) -> ExperimentalGroup | None:
        """Updates an existing ExperimentalGroup."""
        group = self.db.scalar(select(ExperimentalGroup).where(ExperimentalGroup.id == group_id))
        if not group:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(group, key, value)

        self.db.commit()
        return self.get_by_id(group_id)

    def delete(self, group_id: UUID) -> bool:
        """Deletes an ExperimentalGroup by ID."""
        group = self.db.scalar(select(ExperimentalGroup).where(ExperimentalGroup.id == group_id))
        if not group:
            return False
        self.db.delete(group)
        self.db.commit()
        return True
