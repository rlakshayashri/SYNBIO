import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_datasets_end_to_end_demo_flow() -> None:
    """End-to-end integration test demonstrating full demo flow:

    1. Create Project
    2. Upload Problematic CSV Dataset
    3. Retrieve Metadata
    4. Fetch Head Preview
    5. Run Data Quality Validation
    """
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Demo Scientific Project", "description": "End to end test project"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Upload Problematic CSV Dataset
    prob_csv_path = FIXTURES_DIR / "problematic_dataset.csv"
    with open(prob_csv_path, "rb") as f:
        upload_resp = client.post(
            "/api/v1/datasets/upload",
            data={"project_id": project_id, "name": "Problematic Experiment Run"},
            files={"file": ("problematic_dataset.csv", f, "text/csv")},
        )
    assert upload_resp.status_code == 201
    dataset_data = upload_resp.json()
    dataset_id = dataset_data["id"]
    assert dataset_data["row_count"] == 5
    assert dataset_data["column_count"] == 5

    # 3. GET Metadata
    meta_resp = client.get(f"/api/v1/datasets/{dataset_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["name"] == "Problematic Experiment Run"

    # 4. GET Preview
    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=10")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["row_count"] == 5
    assert len(preview_data["columns"]) == 5
    assert len(preview_data["data"]) == 5

    # 5. POST Validate Data Quality Report
    val_resp = client.post(f"/api/v1/datasets/{dataset_id}/validate")
    assert val_resp.status_code == 200
    report = val_resp.json()

    assert report["dataset_id"] == dataset_id
    assert report["overall_status"] == "ERROR"
    assert report["summary"]["empty_columns"] == 1
    assert report["summary"]["missing_values"] >= 1
    assert report["summary"]["duplicate_rows"] == 1
    assert report["summary"]["potential_outliers"] >= 1
    assert len(report["warnings"]) > 0


def test_upload_unsupported_file_type_returns_400() -> None:
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Invalid File Test Project"},
    )
    project_id = proj_resp.json()["id"]

    # 2. Upload invalid txt file
    upload_resp = client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("test.txt", b"plain text content", "text/plain")},
    )
    assert upload_resp.status_code == 400
    assert "UnsupportedFileTypeError" in upload_resp.json()["error"]


def test_nonexistent_dataset_preview_returns_404() -> None:
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/datasets/{fake_id}/preview")
    assert resp.status_code == 404
    assert "DatasetNotFoundError" in resp.json()["error"]
