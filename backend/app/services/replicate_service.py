from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ScientificValidationError
from app.models.experimental_group import ExperimentalGroup
from app.models.replicate import Replicate
from app.schemas.replicate import ReplicateCreate, ReplicateUpdate


class ReplicateService:
    """Service encapsulating database logic for Replicate sample lifecycle management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, replicate_id: UUID) -> Replicate | None:
        """Retrieves a single Replicate by ID."""
        return self.db.scalar(select(Replicate).where(Replicate.id == replicate_id))

    def list_for_group(self, group_id: UUID) -> Sequence[Replicate]:
        """Lists all replicates belonging to a specific ExperimentalGroup."""
        stmt = (
            select(Replicate)
            .where(Replicate.group_id == group_id)
            .order_by(Replicate.created_at.asc())
        )
        return self.db.scalars(stmt).all()

    def create(self, group_id: UUID, schema: ReplicateCreate) -> Replicate:
        """Adds a new Replicate sample to an existing ExperimentalGroup."""
        group = self.db.scalar(select(ExperimentalGroup).where(ExperimentalGroup.id == group_id))
        if not group:
            raise ScientificValidationError(f"Experimental group with ID '{group_id}' not found.")

        replicate = Replicate(
            group_id=group_id,
            replicate_name=schema.replicate_name,
            sample_identifier=schema.sample_identifier,
            row_index=schema.row_index,
            replicate_type=schema.replicate_type,
            metadata_payload=schema.metadata_payload,
        )
        self.db.add(replicate)
        self.db.commit()
        self.db.refresh(replicate)
        return replicate

    def update(self, replicate_id: UUID, schema: ReplicateUpdate) -> Replicate | None:
        """Updates an existing Replicate."""
        replicate = self.get_by_id(replicate_id)
        if not replicate:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(replicate, key, value)

        self.db.commit()
        self.db.refresh(replicate)
        return replicate

    def delete(self, replicate_id: UUID) -> bool:
        """Deletes a Replicate by ID."""
        replicate = self.get_by_id(replicate_id)
        if not replicate:
            return False
        self.db.delete(replicate)
        self.db.commit()
        return True
