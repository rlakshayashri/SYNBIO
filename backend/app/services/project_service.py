from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service encapsulating database logic for Project management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, project_id: UUID) -> Project | None:
        """Retrieves a single project by ID."""
        return self.db.scalar(select(Project).where(Project.id == project_id))

    def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Project]:
        """Lists projects with pagination."""
        stmt = select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
        return self.db.scalars(stmt).all()

    def create(self, schema: ProjectCreate) -> Project:
        """Creates a new Project."""
        project = Project(
            name=schema.name,
            description=schema.description,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: UUID, schema: ProjectUpdate) -> Project | None:
        """Updates an existing Project."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: UUID) -> bool:
        """Deletes a Project by ID."""
        project = self.get_by_id(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
