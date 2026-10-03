from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
)
def create_project(schema: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
    """Creates a new scientific project container."""
    service = ProjectService(db)
    return service.create(schema)


@router.get("", response_model=list[ProjectResponse], summary="List Projects")
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[ProjectResponse]:
    """Lists projects with pagination."""
    service = ProjectService(db)
    return list(service.list_all(skip=skip, limit=limit))


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get Project")
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectResponse:
    """Retrieves a single project by ID."""
    service = ProjectService(db)
    project = service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return project
