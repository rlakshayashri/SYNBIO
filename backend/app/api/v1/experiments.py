from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.comparison import ComparisonCreateRequest, ComparisonResponse
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)
from app.schemas.experimental_group import (
    ExperimentalGroupCreate,
    ExperimentalGroupResponse,
)
from app.schemas.replicate import ReplicateCreate, ReplicateResponse
from app.services.comparison_service import ComparisonService
from app.services.experiment_service import ExperimentService
from app.services.group_service import GroupService
from app.services.replicate_service import ReplicateService

router = APIRouter()


@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Experiment",
)
def create_experiment(schema: ExperimentCreate, db: Session = Depends(get_db)) -> ExperimentResponse:
    """Creates a new Experiment container with optional groups and replicates."""
    service = ExperimentService(db)
    return service.create(schema)


@router.get("", response_model=list[ExperimentResponse], summary="List Experiments")
def list_experiments(
    project_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[ExperimentResponse]:
    """Lists experiments with optional project filtering and pagination."""
    service = ExperimentService(db)
    return list(service.list_all(project_id=project_id, skip=skip, limit=limit))


@router.get("/{experiment_id}", response_model=ExperimentResponse, summary="Get Experiment")
def get_experiment(experiment_id: UUID, db: Session = Depends(get_db)) -> ExperimentResponse:
    """Retrieves a single experiment by ID with groups, replicates, and comparisons."""
    service = ExperimentService(db)
    experiment = service.get_by_id(experiment_id)
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")
    return experiment


@router.patch("/{experiment_id}", response_model=ExperimentResponse, summary="Update Experiment")
def update_experiment(
    experiment_id: UUID, schema: ExperimentUpdate, db: Session = Depends(get_db)
) -> ExperimentResponse:
    """Updates an existing experiment."""
    service = ExperimentService(db)
    experiment = service.update(experiment_id, schema)
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")
    return experiment


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Experiment")
def delete_experiment(experiment_id: UUID, db: Session = Depends(get_db)) -> None:
    """Deletes an experiment by ID."""
    service = ExperimentService(db)
    success = service.delete(experiment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")


@router.post(
    "/{experiment_id}/groups",
    response_model=ExperimentalGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Experimental Group",
)
def add_experimental_group(
    experiment_id: UUID, schema: ExperimentalGroupCreate, db: Session = Depends(get_db)
) -> ExperimentalGroupResponse:
    """Adds a new ExperimentalGroup to an existing experiment."""
    service = GroupService(db)
    return service.create(experiment_id, schema)


@router.post(
    "/groups/{group_id}/replicates",
    response_model=ReplicateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Replicate",
)
def add_replicate(
    group_id: UUID, schema: ReplicateCreate, db: Session = Depends(get_db)
) -> ReplicateResponse:
    """Adds a new Replicate to an existing experimental group."""
    service = ReplicateService(db)
    return service.create(group_id, schema)


@router.post(
    "/{experiment_id}/comparisons",
    response_model=ComparisonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Experimental Comparison",
)
def run_comparison(
    experiment_id: UUID, request: ComparisonCreateRequest, db: Session = Depends(get_db)
) -> ComparisonResponse:
    """Executes group comparison and stores Analysis & Comparison records."""
    service = ComparisonService(db)
    return service.run_comparison(experiment_id, request)
