import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.dataset import Dataset
    from app.models.experiment import Experiment
    from app.models.experimental_factor import ExperimentalFactor

JSONType = JSON().with_variant(JSONB, "postgresql")


class FactorialComparison(Base):
    """FactorialComparison ORM Model persisting two-factor factorial analyses and provenance."""

    __tablename__ = "factorial_comparisons"
    __table_args__ = (
        CheckConstraint(
            "factor_a_id IS NULL OR factor_b_id IS NULL OR factor_a_id != factor_b_id",
            name="ck_factorial_comparisons_distinct_factors",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending", default="pending")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional foreign keys to registered ExperimentalFactors
    factor_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experimental_factors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    factor_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experimental_factors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Dataset column mapping
    factor_a_column: Mapped[str] = mapped_column(String(255), nullable=False)
    factor_b_column: Mapped[str] = mapped_column(String(255), nullable=False)
    measurement_column: Mapped[str] = mapped_column(String(255), nullable=False)

    parameters: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="factorial_comparisons")
    dataset: Mapped["Dataset | None"] = relationship("Dataset")
    analysis: Mapped["Analysis | None"] = relationship(
        "Analysis", back_populates="factorial_comparison", uselist=False
    )
    factor_a: Mapped["ExperimentalFactor | None"] = relationship(
        "ExperimentalFactor", foreign_keys=[factor_a_id]
    )
    factor_b: Mapped["ExperimentalFactor | None"] = relationship(
        "ExperimentalFactor", foreign_keys=[factor_b_id]
    )

    def validate_factor_ownership(self) -> None:
        """Validate that referenced factors belong to the same experiment as the factorial comparison."""
        if self.factor_a and self.factor_a.experiment_id != self.experiment_id:
            raise ValueError(
                f"Factor A (ID: {self.factor_a.id}) belongs to experiment {self.factor_a.experiment_id}, "
                f"not {self.experiment_id}."
            )
        if self.factor_b and self.factor_b.experiment_id != self.experiment_id:
            raise ValueError(
                f"Factor B (ID: {self.factor_b.id}) belongs to experiment {self.factor_b.experiment_id}, "
                f"not {self.experiment_id}."
            )
