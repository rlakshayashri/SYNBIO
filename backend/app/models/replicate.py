import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, UUID

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.experimental_group import ExperimentalGroup

JSONType = JSON().with_variant(JSONB, "postgresql")


class Replicate(Base):
    """Replicate ORM Model representing an individual biological or technical replicate sample."""

    __tablename__ = "replicates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experimental_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    replicate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replicate_type: Mapped[str] = mapped_column(String(50), nullable=False, default="biological")
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    group: Mapped["ExperimentalGroup"] = relationship("ExperimentalGroup", back_populates="replicates")
