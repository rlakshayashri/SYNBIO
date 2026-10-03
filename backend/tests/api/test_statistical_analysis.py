import io
import uuid
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_statistical_analysis_api_flow() -> None:
    """Verifies end-to-end API execution of statistical analysis endpoints."""
    # 1. Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Stat Analysis API Project", "description": "API test project"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Upload Clean CSV Dataset
    clean_csv_path = FIXTURES_DIR / "clean_dataset.csv"
    with open(clean_csv_path, "rb") as f:
        upload_resp = client.post(
            "/api/v1/datasets/upload",
            data={"project_id": project_id, "name": "Stat Test Dataset"},
            files={"file": ("clean_dataset.csv", f, "text/csv")},
        )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 3. POST Correlation Analysis (concentration vs absorbance)
    corr_payload = {
        "category": "correlation",
        "method": "pearson",
        "value_column": "concentration",
        "value_column_2": "absorbance",
        "alpha": 0.05,
    }
    corr_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/statistical-analysis",
        json=corr_payload,
    )
    assert corr_resp.status_code == 200
    corr_data = corr_resp.json()
    assert corr_data["category"] == "correlation"
    assert corr_data["method"] == "pearson"
    assert corr_data["statistic_name"] == "Pearson r"
    assert corr_data["p_value"] is not None
    assert "returned Pearson r =" in corr_data["statement"]

    # 4. Upload Grouped Dataset for Two-Group Comparison
    df_grouped = pd.DataFrame(
        {
            "strain": ["Control"] * 5 + ["Mutant"] * 5,
            "yield_g_l": [10.1, 10.5, 9.8, 10.2, 10.0, 15.2, 14.8, 15.5, 15.0, 14.9],
        }
    )
    csv_bytes = df_grouped.to_csv(index=False).encode("utf-8")
    upload_grouped_resp = client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id, "name": "Grouped Dataset"},
        files={"file": ("grouped.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert upload_grouped_resp.status_code == 201
    grouped_id = upload_grouped_resp.json()["id"]

    # 5. POST Two-Group Comparison (Welch's t-test)
    ttest_payload = {
        "category": "two_group",
        "method": "welch_ttest",
        "value_column": "yield_g_l",
        "group_column": "strain",
        "alpha": 0.05,
    }
    ttest_resp = client.post(
        f"/api/v1/datasets/{grouped_id}/statistical-analysis",
        json=ttest_payload,
    )
    assert ttest_resp.status_code == 200
    ttest_data = ttest_resp.json()
    assert ttest_data["category"] == "two_group"
    assert ttest_data["method"] == "welch_ttest"
    assert ttest_data["statistic_name"] == "Welch t"
    assert ttest_data["effect_size"]["name"] == "Cohen's d"


def test_statistical_analysis_nonexistent_dataset_404() -> None:
    fake_id = str(uuid.uuid4())
    payload = {
        "category": "correlation",
        "method": "pearson",
        "value_column": "x",
        "value_column_2": "y",
    }
    resp = client.post(f"/api/v1/datasets/{fake_id}/statistical-analysis", json=payload)
    assert resp.status_code == 404
    assert "DatasetNotFoundError" in resp.json()["error"]
