import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.dataset import Dataset
from app.models.project import Project
from app.storage.local import LocalStorageService

client = TestClient(app)


@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="API Test Project", description="API Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_dataset(db_session: Session, test_project: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"group,od600\nCTRL,0.21\nCTRL,0.23\nCTRL,0.22\nTRT,0.85\nTRT,0.88\nTRT,0.82\n"
    rel_path = storage.save_file(dataset_id, "api_exp_data.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        name="API Exp Dataset",
        file_name="api_exp_data.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=6,
        column_count=2,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_experiment_api_end_to_end_flow(test_project: Project, test_dataset: Dataset, monkeypatch, tmp_path: Path):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.comparison_service.LocalStorageService", lambda: storage)

    # 1. Create Experiment
    payload = {
        "project_id": str(test_project.id),
        "dataset_id": str(test_dataset.id),
        "name": "Bacterial Growth Assay",
        "organism": "E. coli",
        "condition_type": "Inhibitor Concentration",
        "groups": [
            {
                "name": "Control 0uM",
                "group_code": "CTRL",
                "is_control": True,
                "replicates": [{"replicate_name": "Rep_1"}, {"replicate_name": "Rep_2"}],
            },
            {
                "name": "Treatment 50uM",
                "group_code": "TRT",
                "is_control": False,
                "replicates": [{"replicate_name": "Rep_1"}],
            },
        ],
    }

    res = client.post("/api/v1/experiments", json=payload)
    assert res.status_code == 201
    exp_data = res.json()
    exp_id = exp_data["id"]
    assert exp_data["name"] == "Bacterial Growth Assay"
    assert len(exp_data["groups"]) == 2

    # 2. Get Experiment
    res = client.get(f"/api/v1/experiments/{exp_id}")
    assert res.status_code == 200
    assert res.json()["id"] == exp_id

    # 3. List Experiments
    res = client.get(f"/api/v1/experiments?project_id={test_project.id}")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 4. Add Group
    group_payload = {
        "name": "Treatment 100uM",
        "group_code": "TRT2",
        "is_control": False,
    }
    res = client.post(f"/api/v1/experiments/{exp_id}/groups", json=group_payload)
    assert res.status_code == 201
    group_id = res.json()["id"]
    assert res.json()["group_code"] == "TRT2"

    # 5. Add Replicate
    rep_payload = {
        "replicate_name": "Rep_3",
        "sample_identifier": "SMP_100_3",
    }
    res = client.post(f"/api/v1/experiments/groups/{group_id}/replicates", json=rep_payload)
    assert res.status_code == 201
    assert res.json()["replicate_name"] == "Rep_3"

    # 6. Run Comparison
    comp_payload = {
        "name": "OD600 Comparison",
        "comparison_type": "two_group",
        "group_a_id": exp_data["groups"][0]["id"],
        "group_b_id": exp_data["groups"][1]["id"],
        "measurement_column": "od600",
        "group_column": "group",
    }
    res = client.post(f"/api/v1/experiments/{exp_id}/comparisons", json=comp_payload)
    assert res.status_code == 201
    comp_data = res.json()
    assert comp_data["name"] == "OD600 Comparison"
    assert "statistical_result" in comp_data["result_summary"]


def test_api_same_group_comparison_returns_400(
    test_project: Project, test_dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.comparison_service.LocalStorageService", lambda: storage)

    payload = {
        "project_id": str(test_project.id),
        "dataset_id": str(test_dataset.id),
        "name": "Single Group Assay",
        "groups": [{"name": "Control 0uM", "group_code": "CTRL"}],
    }
    res = client.post("/api/v1/experiments", json=payload)
    assert res.status_code == 201
    exp_data = res.json()
    group_id = exp_data["groups"][0]["id"]

    comp_payload = {
        "name": "Invalid Self Comparison",
        "comparison_type": "two_group",
        "group_a_id": group_id,
        "group_b_id": group_id,
        "measurement_column": "od600",
        "group_column": "group",
    }
    res = client.post(f"/api/v1/experiments/{exp_data['id']}/comparisons", json=comp_payload)
    assert res.status_code == 400
    assert "distinct" in res.json()["detail"].lower()


def test_get_nonexistent_experiment_returns_404():
    res = client.get(f"/api/v1/experiments/{uuid.uuid4()}")
    assert res.status_code == 404
