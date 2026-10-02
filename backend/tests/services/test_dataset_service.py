import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.schemas.project import ProjectCreate
from app.services.dataset_service import DatasetService
from app.services.project_service import ProjectService
from app.services.validation_service import ValidationService
from app.storage.local import LocalStorageService

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def tmp_storage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield LocalStorageService(base_dir=tmp_dir)


def test_dataset_service_upload_and_validation_flow(db_session, tmp_storage) -> None:
    # 1. Create a Project
    project_service = ProjectService(db_session)
    project = project_service.create(ProjectCreate(name="Test Project Service"))

    # 2. Upload clean dataset via DatasetService
    dataset_service = DatasetService(db_session, storage=tmp_storage)
    clean_path = FIXTURES_DIR / "clean_dataset.csv"
    with open(clean_path, "rb") as f:
        file_bytes = f.read()

    dataset = dataset_service.upload_dataset(
        project_id=project.id,
        file_name="clean_dataset.csv",
        file_type="csv",
        file_bytes=file_bytes,
    )

    assert dataset.id is not None
    assert dataset.row_count == 5
    assert dataset.column_count == 4

    # 3. Generate Preview
    preview = dataset_service.get_preview(dataset.id, limit=3)
    assert preview.row_count == 5
    assert preview.preview_rows == 3
    assert len(preview.columns) == 4

    # 4. Run Validation Service
    val_service = ValidationService(db_session, storage=tmp_storage)
    val_result = val_service.run_validation(dataset.id)
    assert val_result.overall_status.value == "PASS"


def test_upload_nonexistent_project_fails(db_session, tmp_storage) -> None:
    import uuid

    dataset_service = DatasetService(db_session, storage=tmp_storage)
    fake_id = uuid.uuid4()
    with pytest.raises(ProjectNotFoundError):
        dataset_service.upload_dataset(
            project_id=fake_id,
            file_name="test.csv",
            file_type="csv",
            file_bytes=b"a,b\n1,2",
        )
