import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.project import Project
from app.schemas.experiment import ExperimentCreate
from app.schemas.experimental_group import ExperimentalGroupCreate
from app.schemas.replicate import ReplicateCreate
from app.services.experiment_dataset_service import ExperimentDatasetService
from app.services.experiment_service import ExperimentService
from app.services.experiment_workspace_service import ExperimentWorkspaceService
from app.storage.local import LocalStorageService


@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="Workspace Test Project", description="Workspace Test Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_dataset(db_session: Session, test_project: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"group,val\nA,1.0\nA,2.0\nB,3.0\nB,4.0\n"
    rel_path = storage.save_file(dataset_id, "workspace_data.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        name="Workspace Dataset",
        file_name="workspace_data.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=4,
        column_count=2,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_get_workspace_summary_success(
    db_session: Session, test_project: Project, test_dataset: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    exp_ds_service = ExperimentDatasetService(db_session, storage=storage)
    workspace_service = ExperimentWorkspaceService(db_session)

    # 1. Create experiment with groups and replicates
    exp = exp_service.create(
        ExperimentCreate(
            project_id=test_project.id,
            name="Workspace Summary Exp",
            status="in_progress",
            objective="Verify workspace summary payload",
            groups=[
                ExperimentalGroupCreate(
                    name="Group A",
                    group_code="A",
                    replicates=[ReplicateCreate(replicate_name="Rep_1")],
                )
            ],
        )
    )

    # 2. Attach dataset
    exp_ds_service.attach_dataset(exp.id, test_dataset.id)

    # 3. Add analysis record linked to experiment
    analysis = Analysis(
        dataset_id=test_dataset.id,
        experiment_id=exp.id,
        analysis_type="validation",
        result={"missing_count": 0},
    )
    db_session.add(analysis)
    db_session.commit()

    # 4. Fetch workspace summary
    ws = workspace_service.get_workspace(exp.id)

    assert ws.experiment.id == exp.id
    assert ws.experiment.name == "Workspace Summary Exp"
    assert ws.experiment.status == "in_progress"
    assert ws.experiment.objective == "Verify workspace summary payload"

    assert len(ws.attached_datasets) == 1
    assert ws.attached_datasets[0].id == test_dataset.id

    assert len(ws.groups) == 1
    assert ws.groups[0].name == "Group A"
    assert len(ws.groups[0].replicates) == 1

    assert len(ws.analyses) == 1
    assert ws.analyses[0].analysis_type == "validation"


def test_get_workspace_nonexistent_experiment_fails(db_session: Session):
    workspace_service = ExperimentWorkspaceService(db_session)
    with pytest.raises(ExperimentNotFoundError):
        workspace_service.get_workspace(uuid.uuid4())
