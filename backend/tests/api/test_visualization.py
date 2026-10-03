import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_visualization_api_histogram_flow() -> None:
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Visualization Test Project"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Upload Clean CSV Dataset
    clean_csv_path = FIXTURES_DIR / "clean_dataset.csv"
    with open(clean_csv_path, "rb") as f:
        upload_resp = client.post(
            "/api/v1/datasets/upload",
            data={"project_id": project_id, "name": "Clean Dataset for Viz"},
            files={"file": ("clean_dataset.csv", f, "text/csv")},
        )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 3. POST /visualizations (Histogram)
    hist_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/visualizations",
        json={"plot_type": "histogram", "column": "absorbance"},
    )
    assert hist_resp.status_code == 200
    report = hist_resp.json()

    assert report["dataset_id"] == dataset_id
    assert report["plot_type"] == "histogram"
    assert report["x_axis"] == "absorbance"
    assert len(report["traces"]) == 1
    assert len(report["traces"][0]["x"]) == 5


def test_visualization_api_scatter_flow() -> None:
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Scatter Plot Test Project"},
    )
    project_id = proj_resp.json()["id"]

    # 2. Upload Clean CSV Dataset
    clean_csv_path = FIXTURES_DIR / "clean_dataset.csv"
    with open(clean_csv_path, "rb") as f:
        upload_resp = client.post(
            "/api/v1/datasets/upload",
            data={"project_id": project_id},
            files={"file": ("clean_dataset.csv", f, "text/csv")},
        )
    dataset_id = upload_resp.json()["id"]

    # 3. POST /visualizations (Scatter)
    scatter_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/visualizations",
        json={
            "plot_type": "scatter",
            "x_column": "concentration",
            "y_column": "absorbance",
        },
    )
    assert scatter_resp.status_code == 200
    report = scatter_resp.json()

    assert report["plot_type"] == "scatter"
    assert report["x_axis"] == "concentration"
    assert report["y_axis"] == "absorbance"


def test_visualization_nonexistent_dataset_404() -> None:
    fake_id = str(uuid.uuid4())
    resp = client.post(
        f"/api/v1/datasets/{fake_id}/visualizations",
        json={"plot_type": "histogram", "column": "absorbance"},
    )
    assert resp.status_code == 404
    assert "DatasetNotFoundError" in resp.json()["error"]
