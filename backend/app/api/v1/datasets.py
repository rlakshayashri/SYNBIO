from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError
from app.db.session import get_db
from app.schemas.dataset import DatasetPreviewResponse, DatasetResponse
from app.schemas.validation import ValidationResult
from app.services.dataset_service import DatasetService
from app.services.validation_service import ValidationService

router = APIRouter()


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Dataset File",
)
def upload_dataset(
    project_id: UUID = Form(..., description="ID of the associated Project"),
    name: str | None = Form(None, description="Optional custom display name"),
    file: UploadFile = File(..., description="CSV or Excel file"),
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """Uploads a CSV or XLSX dataset file, extracts metadata, saves to storage, and persists DB record."""
    file_bytes = file.file.read()
    file_name = file.filename or "uploaded_file"
    file_type = file.content_type or file_name.split(".")[-1]

    service = DatasetService(db)
    return service.upload_dataset(
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        file_bytes=file_bytes,
        name=name,
    )


@router.get("", response_model=list[DatasetResponse], summary="List Datasets")
def list_datasets(
    project_id: UUID = Query(..., description="Project ID to list datasets for"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[DatasetResponse]:
    """Lists datasets associated with a given Project."""
    service = DatasetService(db)
    return list(service.list_by_project(project_id=project_id, skip=skip, limit=limit))


@router.get("/{dataset_id}", response_model=DatasetResponse, summary="Get Dataset Metadata")
def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)) -> DatasetResponse:
    """Retrieves dataset metadata by ID."""
    service = DatasetService(db)
    dataset = service.get_by_id(dataset_id)
    if not dataset:
        raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")
    return dataset


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    summary="Preview Dataset Head Rows",
)
def get_dataset_preview(
    dataset_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Number of preview rows to return"),
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    """Returns head preview rows and column metrics (dtypes, null counts) for a dataset."""
    service = DatasetService(db)
    return service.get_preview(dataset_id=dataset_id, limit=limit)


@router.post(
    "/{dataset_id}/validate",
    response_model=ValidationResult,
    summary="Validate Dataset & Generate Quality Report",
)
def validate_dataset(dataset_id: UUID, db: Session = Depends(get_db)) -> ValidationResult:
    """Executes data quality checks (missing values, duplicates, dtypes, empty columns, outliers) on a dataset."""
    service = ValidationService(db)
    return service.run_validation(dataset_id=dataset_id)
