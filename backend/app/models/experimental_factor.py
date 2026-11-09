import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.experiment import Experiment
    from app.models.factor_level import FactorLevel


class ExperimentalFactor(Base):
    """ExperimentalFactor ORM Model representing an independent categorical variable in an experiment."""

    __tablename__ = "experimental_factors"
    __table_args__ = (
        UniqueConstraint("experiment_id", "name", name="uq_experimental_factors_experiment_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    factor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="factors")
    levels: Mapped[list["FactorLevel"]] = relationship(
        "FactorLevel",
        back_populates="factor",
        cascade="all, delete-orphan",
        order_by="FactorLevel.order_index",
    )
