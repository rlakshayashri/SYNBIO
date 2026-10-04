import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.project import Project
from app.schemas.experiment import ExperimentCreate, ExperimentResponse, ExperimentUpdate
from app.services.experiment_service import ExperimentService
from app.storage.local import LocalStorageService


@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="Phase 1 Test Project", description="Phase 1 Test Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_dataset_1(db_session: Session, test_project: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"val1,val2\n1.0,2.0\n3.0,4.0\n"
    rel_path = storage.save_file(dataset_id, "data1.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        name="Dataset 1",
        file_name="data1.csv",
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
def test_dataset_2(db_session: Session, test_project: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"val1,val2\n5.0,6.0\n7.0,8.0\n"
    rel_path = storage.save_file(dataset_id, "data2.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        name="Dataset 2",
        file_name="data2.csv",
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


def test_experiment_status_and_objective_defaults(db_session: Session, test_project: Project):
    """Test that status defaults to 'draft' and objective is optional."""
    service = ExperimentService(db_session)
    create_schema = ExperimentCreate(
        project_id=test_project.id,
        name="Default Status Exp",
        objective="Verify heat shock promoter",
    )

    exp = service.create(create_schema)
    assert exp.status == "draft"
    assert exp.objective == "Verify heat shock promoter"

    # Test update status to in_progress
    updated = service.update(exp.id, ExperimentUpdate(status="in_progress", objective="Updated objective"))
    assert updated is not None
    assert updated.status == "in_progress"
    assert updated.objective == "Updated objective"


def test_dataset_experiment_relationship(
    db_session: Session, test_project: Project, test_dataset_1: Dataset, test_dataset_2: Dataset
):
    """Test that multiple datasets can belong to an experiment, remain standalone, or detach cleanly."""
    exp = Experiment(
        project_id=test_project.id,
        name="Multi Dataset Exp",
        status="in_progress",
        objective="Test multi dataset attachment",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    # Standalone initial state
    assert test_dataset_1.experiment_id is None
    assert len(exp.datasets) == 0

    # Attach dataset 1 & 2
    test_dataset_1.experiment_id = exp.id
    test_dataset_2.experiment_id = exp.id
    db_session.commit()

    db_session.refresh(exp)
    assert len(exp.datasets) == 2
    assert test_dataset_1 in exp.datasets
    assert test_dataset_2 in exp.datasets

    # Detach dataset 1
    test_dataset_1.experiment_id = None
    db_session.commit()

    db_session.refresh(exp)
    assert len(exp.datasets) == 1
    assert test_dataset_1.experiment_id is None


def test_analysis_experiment_relationship(
    db_session: Session, test_project: Project, test_dataset_1: Dataset
):
    """Test that analyses can belong to an experiment or remain standalone."""
    exp = Experiment(
        project_id=test_project.id,
        name="Analysis Traceability Exp",
        status="completed",
        objective="Test analysis experiment provenance",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    # Create standalone analysis
    standalone_analysis = Analysis(
        dataset_id=test_dataset_1.id,
        analysis_type="descriptive_statistics",
        parameters={"columns": ["val1"]},
        result={"mean": 2.0},
    )
    db_session.add(standalone_analysis)

    # Create experiment-scoped analysis
    exp_analysis = Analysis(
        dataset_id=test_dataset_1.id,
        experiment_id=exp.id,
        analysis_type="welch_ttest",
        parameters={"measurement_column": "val1"},
        result={"p_value": 0.01},
    )
    db_session.add(exp_analysis)
    db_session.commit()

    db_session.refresh(exp)
    assert standalone_analysis.experiment_id is None
    assert exp_analysis.experiment_id == exp.id
    assert len(exp.analyses) == 1
    assert exp.analyses[0].id == exp_analysis.id


def test_experiment_response_schema_serialization(db_session: Session, test_project: Project):
    """Test Pydantic serialization of Experiment response with status and objective."""
    exp = Experiment(
        project_id=test_project.id,
        name="Pydantic Serialization Test",
        status="completed",
        objective="Hypothesis testing for GFP",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    response = ExperimentResponse.model_validate(exp)
    assert response.status == "completed"
    assert response.objective == "Hypothesis testing for GFP"
