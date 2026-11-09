from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError, ScientificValidationError
from app.models.experiment import Experiment
from app.models.experimental_factor import ExperimentalFactor
from app.models.factor_level import FactorLevel
from app.schemas.factor import ExperimentalFactorCreate, ExperimentalFactorUpdate


class FactorService:
    """Service encapsulating ExperimentalFactor and FactorLevel lifecycle."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_factor(self, experiment_id: UUID, schema: ExperimentalFactorCreate) -> ExperimentalFactor:
        """Creates an experimental factor with optional initial levels."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        # Check unique factor name within experiment
        existing = self.db.scalar(
            select(ExperimentalFactor).where(
                ExperimentalFactor.experiment_id == experiment_id,
                ExperimentalFactor.name == schema.name,
            )
        )
        if existing:
            raise ScientificValidationError(
                f"Factor with name '{schema.name}' already exists in experiment '{experiment_id}'."
            )

        factor = ExperimentalFactor(
            experiment_id=experiment_id,
            name=schema.name,
            description=schema.description,
            factor_type=schema.factor_type,
        )
        self.db.add(factor)
        self.db.flush()

        # Add initial levels if provided
        for lvl in schema.levels:
            level_obj = FactorLevel(
                factor_id=factor.id,
                name=lvl.name,
                description=lvl.description,
                order_index=lvl.order_index,
            )
            self.db.add(level_obj)

        self.db.commit()
        return self.get_factor(factor.id, experiment_id=experiment_id)  # type: ignore[return-value]

    def get_factor(self, factor_id: UUID, experiment_id: UUID | None = None) -> ExperimentalFactor | None:
        """Retrieves a single experimental factor by ID with levels populated."""
        stmt = (
            select(ExperimentalFactor)
            .options(joinedload(ExperimentalFactor.levels))
            .where(ExperimentalFactor.id == factor_id)
        )
        if experiment_id:
            stmt = stmt.where(ExperimentalFactor.experiment_id == experiment_id)
        return self.db.scalar(stmt)

    def list_factors(self, experiment_id: UUID) -> Sequence[ExperimentalFactor]:
        """Lists all experimental factors for an experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        stmt = (
            select(ExperimentalFactor)
            .options(joinedload(ExperimentalFactor.levels))
            .where(ExperimentalFactor.experiment_id == experiment_id)
            .order_by(ExperimentalFactor.created_at.asc())
        )
        return self.db.scalars(stmt).unique().all()

    def update_factor(
        self, experiment_id: UUID, factor_id: UUID, schema: ExperimentalFactorUpdate
    ) -> ExperimentalFactor | None:
        """Updates metadata on an existing experimental factor."""
        factor = self.get_factor(factor_id, experiment_id=experiment_id)
        if not factor:
            return None

        if schema.name is not None and schema.name != factor.name:
            # Check uniqueness
            existing = self.db.scalar(
                select(ExperimentalFactor).where(
                    ExperimentalFactor.experiment_id == experiment_id,
                    ExperimentalFactor.name == schema.name,
                    ExperimentalFactor.id != factor_id,
                )
            )
            if existing:
                raise ScientificValidationError(
                    f"Factor with name '{schema.name}' already exists in experiment '{experiment_id}'."
                )
            factor.name = schema.name

        if schema.description is not None:
            factor.description = schema.description
        if schema.factor_type is not None:
            factor.factor_type = schema.factor_type

        self.db.commit()
        return self.get_factor(factor_id, experiment_id=experiment_id)

    def delete_factor(self, experiment_id: UUID, factor_id: UUID) -> bool:
        """Deletes an experimental factor and cascades to its levels."""
        factor = self.get_factor(factor_id, experiment_id=experiment_id)
        if not factor:
            return False

        self.db.delete(factor)
        self.db.commit()
        return True
