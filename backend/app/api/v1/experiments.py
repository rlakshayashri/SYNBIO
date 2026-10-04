from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.comparison import ComparisonCreateRequest, ComparisonResponse
from app.schemas.dataset import DatasetResponse
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
    ExperimentWorkspaceResponse,
)
from app.schemas.experimental_group import (
    ExperimentalGroupCreate,
    ExperimentalGroupResponse,
)
from app.schemas.replicate import ReplicateCreate, ReplicateResponse
from app.services.comparison_service import ComparisonService
from app.services.experiment_dataset_service import ExperimentDatasetService
from app.services.experiment_service import ExperimentService
from app.services.experiment_workspace_service import ExperimentWorkspaceService
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


@router.post(
    "/{experiment_id}/datasets/{dataset_id}/attach",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach Dataset to Experiment",
)
def attach_dataset(
    experiment_id: UUID, dataset_id: UUID, db: Session = Depends(get_db)
) -> DatasetResponse:
    """Attaches an existing dataset to an experiment."""
    service = ExperimentDatasetService(db)
    return service.attach_dataset(experiment_id, dataset_id)


@router.delete(
    "/{experiment_id}/datasets/{dataset_id}/detach",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
    summary="Detach Dataset from Experiment",
)
def detach_dataset(
    experiment_id: UUID, dataset_id: UUID, db: Session = Depends(get_db)
) -> DatasetResponse:
    """Detaches a dataset from an experiment."""
    service = ExperimentDatasetService(db)
    return service.detach_dataset(experiment_id, dataset_id)


@router.get(
    "/{experiment_id}/datasets",
    response_model=list[DatasetResponse],
    summary="List Attached Datasets",
)
def list_attached_datasets(
    experiment_id: UUID, db: Session = Depends(get_db)
) -> list[DatasetResponse]:
    """Lists all datasets attached to an experiment."""
    service = ExperimentDatasetService(db)
    return list(service.list_attached_datasets(experiment_id))


@router.post(
    "/{experiment_id}/datasets/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Attach Dataset",
)
def upload_and_attach_dataset(
    experiment_id: UUID,
    name: str | None = Form(None, description="Optional custom display name"),
    file: UploadFile = File(..., description="CSV or Excel file"),
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """Uploads a dataset file and attaches it to the specified experiment."""
    file_bytes = file.file.read()
    file_name = file.filename or "uploaded_file"
    file_type = file.content_type or file_name.split(".")[-1]

    service = ExperimentDatasetService(db)
    return service.upload_and_attach(
        experiment_id=experiment_id,
        file_name=file_name,
        file_type=file_type,
        file_bytes=file_bytes,
        name=name,
    )


@router.get(
    "/{experiment_id}/workspace",
    response_model=ExperimentWorkspaceResponse,
    summary="Get Experiment Workspace",
)
def get_experiment_workspace(
    experiment_id: UUID, db: Session = Depends(get_db)
) -> ExperimentWorkspaceResponse:
    """Retrieves lightweight metadata summaries for the Experiment Workspace view."""
    service = ExperimentWorkspaceService(db)
    return service.get_workspace(experiment_id)

