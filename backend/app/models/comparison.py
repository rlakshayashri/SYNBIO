import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.experiment import Experiment
    from app.models.experimental_group import ExperimentalGroup

JSONType = JSON().with_variant(JSONB, "postgresql")


class Comparison(Base):
    """Comparison ORM Model representing a scientific comparison between experimental groups."""

    __tablename__ = "comparisons"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    comparison_type: Mapped[str] = mapped_column(String(50), nullable=False)
    group_a_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experimental_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    group_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experimental_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    measurement_column: Mapped[str] = mapped_column(String(255), nullable=False)
    group_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="comparisons")
    analysis: Mapped["Analysis | None"] = relationship("Analysis", back_populates="comparison")
    group_a: Mapped["ExperimentalGroup | None"] = relationship("ExperimentalGroup", foreign_keys=[group_a_id])
    group_b: Mapped["ExperimentalGroup | None"] = relationship("ExperimentalGroup", foreign_keys=[group_b_id])
