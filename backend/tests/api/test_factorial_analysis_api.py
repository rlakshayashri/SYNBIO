import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.project import Project
from app.storage.local import LocalStorageService

client = TestClient(app)


@pytest.fixture
def project(db_session: Session) -> Project:
    p = Project(name="API Factorial Project", description="API testing for Module 9")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def experiment(db_session: Session, project: Project) -> Experiment:
    exp = Experiment(
        project_id=project.id,
        name="CRISPR Factorial Experiment",
        status="in_progress",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def other_experiment(db_session: Session, project: Project) -> Experiment:
    exp = Experiment(
        project_id=project.id,
        name="Other Project Experiment",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def dataset(db_session: Session, project: Project, experiment: Experiment, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    # 2x2 factorial dataset: Strain (WT, MUT) x Treatment (DMSO, DRUG)
    csv_content = (
        "strain,treatment,yield\n"
        "WT,DMSO,50.1\nWT,DMSO,52.3\nWT,DMSO,51.0\n"
        "WT,DRUG,65.0\nWT,DRUG,67.2\nWT,DRUG,66.1\n"
        "MUT,DMSO,40.2\nMUT,DMSO,41.5\nMUT,DMSO,40.8\n"
        "MUT,DRUG,85.2\nMUT,DRUG,88.1\nMUT,DRUG,86.4\n"
    )
    file_bytes = csv_content.encode("utf-8")
    rel_path = storage.save_file(dataset_id, "crispr_data.csv", file_bytes)

    ds = Dataset(
        id=dataset_id,
        project_id=project.id,
        experiment_id=experiment.id,
        name="CRISPR Expression",
        file_name="crispr_data.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=12,
        column_count=3,
        storage_path=rel_path,
    )
    db_session.add(ds)
    experiment.dataset_id = ds.id
    db_session.commit()
    db_session.refresh(ds)
    db_session.refresh(experiment)
    return ds


# 1. Successful execution and response schema validation
def test_api_run_factorial_comparison_success(
    project: Project, experiment: Experiment, dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.factorial_analysis_service.LocalStorageService", lambda: storage)

    payload = {
        "name": "Strain x Treatment ANOVA",
        "description": "CRISPR yield response across strains and treatments",
        "dataset_id": str(dataset.id),
        "factor_a_column": "strain",
        "factor_b_column": "treatment",
        "measurement_column": "yield",
        "alpha": 0.05,
        "post_hoc_method": "tukey",
        "check_assumptions": True,
    }

    res = client.post(f"/api/v1/experiments/{experiment.id}/factorial-comparisons", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["id"] is not None
    assert data["experiment_id"] == str(experiment.id)
    assert data["dataset_id"] == str(dataset.id)
    assert data["status"] == "completed"
    assert data["name"] == "Strain x Treatment ANOVA"
    assert data["analysis_id"] is not None

    # Verify structured typed two_way_anova_result
    anova = data["two_way_anova_result"]
    assert anova is not None
    assert "strain" in anova["effects"]
    assert "treatment" in anova["effects"]
    assert "strain \u00d7 treatment" in anova["effects"]
    assert anova["is_balanced"] is True
    assert "scientific_statement" in anova


# 2. Retrieval and listing of factorial comparisons
def test_api_get_and_list_factorial_comparisons(
    project: Project, experiment: Experiment, dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.factorial_analysis_service.LocalStorageService", lambda: storage)

    payload = {
        "name": "First Comparison",
        "dataset_id": str(dataset.id),
        "factor_a_column": "strain",
        "factor_b_column": "treatment",
        "measurement_column": "yield",
    }
    create_res = client.post(f"/api/v1/experiments/{experiment.id}/factorial-comparisons", json=payload)
    assert create_res.status_code == 201
    comp_id = create_res.json()["id"]

    # List endpoint
    list_res = client.get(f"/api/v1/experiments/{experiment.id}/factorial-comparisons")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(item["id"] == comp_id for item in items)

    # Get single endpoint
    get_res = client.get(f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{comp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == comp_id


# 3. Update and delete lifecycle via API
def test_api_update_and_delete_factorial_comparison(
    project: Project, experiment: Experiment, dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.factorial_analysis_service.LocalStorageService", lambda: storage)

    payload = {
        "name": "Before Update",
        "dataset_id": str(dataset.id),
        "factor_a_column": "strain",
        "factor_b_column": "treatment",
        "measurement_column": "yield",
    }
    create_res = client.post(f"/api/v1/experiments/{experiment.id}/factorial-comparisons", json=payload)
    comp_id = create_res.json()["id"]

    # PATCH update
    update_payload = {"name": "After Update", "description": "New description"}
    patch_res = client.patch(
        f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{comp_id}", json=update_payload
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "After Update"
    assert patch_res.json()["description"] == "New description"

    # DELETE
    del_res = client.delete(f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{comp_id}")
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{comp_id}")
    assert get_res.status_code == 404


# 4. Cross-experiment access isolation
def test_api_cross_experiment_access_restrictions(
    project: Project,
    experiment: Experiment,
    other_experiment: Experiment,
    dataset: Dataset,
    monkeypatch,
    tmp_path: Path,
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.factorial_analysis_service.LocalStorageService", lambda: storage)

    payload = {
        "name": "Exp 1 Comparison",
        "dataset_id": str(dataset.id),
        "factor_a_column": "strain",
        "factor_b_column": "treatment",
        "measurement_column": "yield",
    }
    create_res = client.post(f"/api/v1/experiments/{experiment.id}/factorial-comparisons", json=payload)
    comp_id = create_res.json()["id"]

    # Trying to access via other_experiment should return 404
    get_res = client.get(f"/api/v1/experiments/{other_experiment.id}/factorial-comparisons/{comp_id}")
    assert get_res.status_code == 404

    # Trying to delete via other_experiment should return 404
    del_res = client.delete(f"/api/v1/experiments/{other_experiment.id}/factorial-comparisons/{comp_id}")
    assert del_res.status_code == 404


# 5. Scientific validation errors return HTTP 400
def test_api_validation_errors_return_400(
    project: Project, experiment: Experiment, dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.factorial_analysis_service.LocalStorageService", lambda: storage)

    # Missing column returns 400
    bad_payload = {
        "name": "Bad Col",
        "dataset_id": str(dataset.id),
        "factor_a_column": "nonexistent",
        "factor_b_column": "treatment",
        "measurement_column": "yield",
    }
    res = client.post(f"/api/v1/experiments/{experiment.id}/factorial-comparisons", json=bad_payload)
    assert res.status_code == 400
    assert "not found in dataset" in res.json()["detail"].lower()


# 6. Experimental Factor endpoints CRUD
def test_api_factor_endpoints_crud(experiment: Experiment):
    factor_payload = {
        "name": "IPTG Inducer",
        "description": "Millimolar concentration of IPTG",
        "factor_type": "chemical",
        "levels": [
            {"name": "0mM", "description": "No induction", "order_index": 0},
            {"name": "1mM", "description": "High induction", "order_index": 1},
        ],
    }

    # Create Factor
    create_res = client.post(f"/api/v1/experiments/{experiment.id}/factors", json=factor_payload)
    assert create_res.status_code == 201
    factor_data = create_res.json()
    assert factor_data["name"] == "IPTG Inducer"
    assert len(factor_data["levels"]) == 2
    factor_id = factor_data["id"]

    # List Factors
    list_res = client.get(f"/api/v1/experiments/{experiment.id}/factors")
    assert list_res.status_code == 200
    factors = list_res.json()
    assert len(factors) >= 1
    assert any(f["id"] == factor_id for f in factors)

    # Delete Factor
    del_res = client.delete(f"/api/v1/experiments/{experiment.id}/factors/{factor_id}")
    assert del_res.status_code == 204


# 7. Regression test for existing statistical analysis endpoints
def test_regression_existing_statistical_analysis_endpoint(
    project: Project, experiment: Experiment, dataset: Dataset, monkeypatch, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr("app.services.comparison_service.LocalStorageService", lambda: storage)

    # Run Module 6 group comparison
    comp_payload = {
        "name": "Regression Two-Group Comparison",
        "comparison_type": "two_group",
        "measurement_column": "yield",
        "group_column": "strain",
        "method": "welch_ttest",
    }
    res = client.post(f"/api/v1/experiments/{experiment.id}/comparisons", json=comp_payload)
    assert res.status_code == 201
    assert "statistical_result" in res.json()["result_summary"]
