from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisUpdate


class AnalysisService:
    """Service encapsulating database logic for Analysis execution records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, analysis_id: UUID) -> Analysis | None:
        """Retrieves a single analysis record by ID."""
        return self.db.scalar(select(Analysis).where(Analysis.id == analysis_id))

    def list_by_dataset(self, dataset_id: UUID, skip: int = 0, limit: int = 100) -> Sequence[Analysis]:
        """Lists analyses run for a specific dataset."""
        stmt = (
            select(Analysis)
            .where(Analysis.dataset_id == dataset_id)
            .offset(skip)
            .limit(limit)
            .order_by(Analysis.created_at.desc())
        )
        return self.db.scalars(stmt).all()

    def create(self, schema: AnalysisCreate) -> Analysis:
        """Creates a new Analysis record."""
        analysis = Analysis(
            dataset_id=schema.dataset_id,
            analysis_type=schema.analysis_type,
            parameters=schema.parameters,
            result=schema.result,
            software_version=schema.software_version,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def update(self, analysis_id: UUID, schema: AnalysisUpdate) -> Analysis | None:
        """Updates analysis output or parameters."""
        analysis = self.get_by_id(analysis_id)
        if not analysis:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(analysis, key, value)

        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def delete(self, analysis_id: UUID) -> bool:
        """Deletes an analysis record by ID."""
        analysis = self.get_by_id(analysis_id)
        if not analysis:
            return False
        self.db.delete(analysis)
        self.db.commit()
        return True
