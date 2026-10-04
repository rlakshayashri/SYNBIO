import io
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.project import Project

client = TestClient(app)



@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="API Test Project", description="API Test Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_experiment(db_session: Session, test_project: Project) -> Experiment:
    exp = Experiment(
        project_id=test_project.id,
        name="API Test Experiment",
        status="in_progress",
        objective="Test workspace API endpoints",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def test_dataset(db_session: Session, test_project: Project) -> Dataset:
    dataset = Dataset(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="API Test Dataset",
        file_name="api_data.csv",
        file_type="csv",
        file_size=100,
        row_count=5,
        column_count=2,
        storage_path="datasets/api_data.csv",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_api_attach_and_detach_dataset(
    test_experiment: Experiment, test_dataset: Dataset
):
    # Attach dataset
    attach_url = f"/api/v1/experiments/{test_experiment.id}/datasets/{test_dataset.id}/attach"
    res_attach = client.post(attach_url)
    assert res_attach.status_code == status.HTTP_200_OK
    data_attach = res_attach.json()
    assert data_attach["experiment_id"] == str(test_experiment.id)

    # List attached datasets
    list_url = f"/api/v1/experiments/{test_experiment.id}/datasets"
    res_list = client.get(list_url)
    assert res_list.status_code == status.HTTP_200_OK
    data_list = res_list.json()
    assert len(data_list) == 1
    assert data_list[0]["id"] == str(test_dataset.id)

    # Detach dataset
    detach_url = f"/api/v1/experiments/{test_experiment.id}/datasets/{test_dataset.id}/detach"
    res_detach = client.delete(detach_url)
    assert res_detach.status_code == status.HTTP_200_OK
    data_detach = res_detach.json()
    assert data_detach["experiment_id"] is None


def test_api_upload_and_attach_dataset(
    test_experiment: Experiment
):
    upload_url = f"/api/v1/experiments/{test_experiment.id}/datasets/upload"
    file_content = b"sample,conc\nS1,10.1\nS2,12.3\n"
    files = {"file": ("upload_test.csv", io.BytesIO(file_content), "text/csv")}
    data = {"name": "Uploaded Experiment Dataset"}

    res = client.post(upload_url, files=files, data=data)
    assert res.status_code == status.HTTP_201_CREATED
    dataset_data = res.json()
    assert dataset_data["name"] == "Uploaded Experiment Dataset"
    assert dataset_data["experiment_id"] == str(test_experiment.id)
    assert dataset_data["row_count"] == 2


def test_api_get_experiment_workspace(
    test_experiment: Experiment, test_dataset: Dataset
):
    # 1. Attach dataset
    attach_url = f"/api/v1/experiments/{test_experiment.id}/datasets/{test_dataset.id}/attach"
    client.post(attach_url)

    # 2. Get workspace summary
    ws_url = f"/api/v1/experiments/{test_experiment.id}/workspace"
    res = client.get(ws_url)
    assert res.status_code == status.HTTP_200_OK

    ws_data = res.json()
    assert "experiment" in ws_data
    assert ws_data["experiment"]["id"] == str(test_experiment.id)
    assert ws_data["experiment"]["status"] == "in_progress"
    assert ws_data["experiment"]["objective"] == "Test workspace API endpoints"

    assert "attached_datasets" in ws_data
    assert len(ws_data["attached_datasets"]) == 1
    assert ws_data["attached_datasets"][0]["id"] == str(test_dataset.id)

    assert "groups" in ws_data
    assert "comparisons" in ws_data
    assert "analyses" in ws_data
