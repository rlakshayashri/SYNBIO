import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_statistics_api_endpoint_flow() -> None:
    """Integration test for POST /api/v1/datasets/{id}/statistics endpoint."""
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Statistics Test Project"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Upload Clean CSV Dataset
    clean_csv_path = FIXTURES_DIR / "clean_dataset.csv"
    with open(clean_csv_path, "rb") as f:
        upload_resp = client.post(
            "/api/v1/datasets/upload",
            data={"project_id": project_id, "name": "Clean Dataset for Stats"},
            files={"file": ("clean_dataset.csv", f, "text/csv")},
        )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 3. POST /statistics endpoint
    stats_resp = client.post(f"/api/v1/datasets/{dataset_id}/statistics")
    assert stats_resp.status_code == 200
    report = stats_resp.json()

    assert report["dataset_id"] == dataset_id
    assert report["row_count"] == 5
    assert report["numeric_column_count"] == 3
    assert report["non_numeric_column_count"] == 1
    assert "sample_id" in report["skipped_columns"]

    stat_cols = [s["column"] for s in report["statistics"]]
    assert "concentration" in stat_cols
    assert "temperature" in stat_cols
    assert "absorbance" in stat_cols


def test_statistics_nonexistent_dataset_404() -> None:
    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/v1/datasets/{fake_id}/statistics")
    assert resp.status_code == 404
    assert "DatasetNotFoundError" in resp.json()["error"]
