import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DatasetNotFoundError,
    ExperimentNotFoundError,
    ScientificValidationError,
)
from app.models.dataset import Dataset
from app.models.project import Project
from app.schemas.experiment import ExperimentCreate
from app.services.experiment_dataset_service import ExperimentDatasetService
from app.services.experiment_service import ExperimentService
from app.storage.local import LocalStorageService


@pytest.fixture
def test_project_a(db_session: Session) -> Project:
    project = Project(name="Project A", description="Project A Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_project_b(db_session: Session) -> Project:
    project = Project(name="Project B", description="Project B Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_dataset_a(db_session: Session, test_project_a: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"col1,col2\n10,20\n30,40\n"
    rel_path = storage.save_file(dataset_id, "data_a.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project_a.id,
        name="Dataset A",
        file_name="data_a.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=2,
        column_count=2,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


@pytest.fixture
def test_dataset_b(db_session: Session, test_project_b: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"col1,col2\n50,60\n"
    rel_path = storage.save_file(dataset_id, "data_b.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project_b.id,
        name="Dataset B",
        file_name="data_b.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=1,
        column_count=2,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_attach_and_detach_dataset(
    db_session: Session, test_project_a: Project, test_dataset_a: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    exp_ds_service = ExperimentDatasetService(db_session, storage=storage)

    exp = exp_service.create(ExperimentCreate(project_id=test_project_a.id, name="Attach Exp"))

    # Initial state: dataset not attached
    assert test_dataset_a.experiment_id is None

    # Attach dataset
    attached = exp_ds_service.attach_dataset(exp.id, test_dataset_a.id)
    assert attached.experiment_id == exp.id

    # List attached
    attached_list = exp_ds_service.list_attached_datasets(exp.id)
    assert len(attached_list) == 1
    assert attached_list[0].id == test_dataset_a.id

    # Detach dataset
    detached = exp_ds_service.detach_dataset(exp.id, test_dataset_a.id)
    assert detached.experiment_id is None

    attached_list_after = exp_ds_service.list_attached_datasets(exp.id)
    assert len(attached_list_after) == 0


def test_attach_cross_project_fails(
    db_session: Session, test_project_a: Project, test_dataset_b: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    exp_ds_service = ExperimentDatasetService(db_session, storage=storage)

    exp_a = exp_service.create(ExperimentCreate(project_id=test_project_a.id, name="Exp Project A"))

    with pytest.raises(ScientificValidationError, match="does not match experiment project"):
        exp_ds_service.attach_dataset(exp_a.id, test_dataset_b.id)


def test_attach_nonexistent_experiment_or_dataset(
    db_session: Session, test_project_a: Project, test_dataset_a: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    exp_ds_service = ExperimentDatasetService(db_session, storage=storage)

    exp_a = exp_service.create(ExperimentCreate(project_id=test_project_a.id, name="Exp A"))

    with pytest.raises(ExperimentNotFoundError):
        exp_ds_service.attach_dataset(uuid.uuid4(), test_dataset_a.id)

    with pytest.raises(DatasetNotFoundError):
        exp_ds_service.attach_dataset(exp_a.id, uuid.uuid4())


def test_upload_and_attach_delegation(
    db_session: Session, test_project_a: Project, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    exp_ds_service = ExperimentDatasetService(db_session, storage=storage)

    exp = exp_service.create(ExperimentCreate(project_id=test_project_a.id, name="Upload & Attach Exp"))

    csv_content = b"sample,measurement\nS1,12.5\nS2,14.8\nS3,13.2\n"
    dataset = exp_ds_service.upload_and_attach(
        experiment_id=exp.id,
        file_name="assay_data.csv",
        file_type="csv",
        file_bytes=csv_content,
        name="Assay Measurements",
    )

    assert dataset.id is not None
    assert dataset.project_id == test_project_a.id
    assert dataset.experiment_id == exp.id
    assert dataset.name == "Assay Measurements"
    assert dataset.row_count == 3
