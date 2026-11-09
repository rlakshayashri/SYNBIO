import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.factorial_comparison import FactorialComparison
from app.models.project import Project
from app.storage.local import LocalStorageService


def test_module_9_complete_e2e_workflow(
    db_session: Session, tmp_path: Path, monkeypatch
) -> None:
    """Executes the complete 13-step End-to-End integration verification for SynDataX Module 9:

    1. Prepare test experiment
    2. Register two conceptual experimental factors with levels via API
    3. Prepare and link a 2x2 factorial dataset
    4. Map conceptual factors to dataset columns & select response column
    5. Execute factorial analysis via API
    6. Verify saved Analysis and FactorialComparison records are consistent
    7. Retrieve saved analysis via GET endpoint
    8. Generate structured JSON experiment report and verify persistence
    9. Render and verify Markdown report with Section 9
    10. Verify JSON export attachment
    11. Verify Markdown export attachment
    12. Verify invalid run leaves no phantom records (atomicity)
    13. Verify clean deletion cascade
    """
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    monkeypatch.setattr(
        "app.services.factorial_analysis_service.LocalStorageService", lambda: storage
    )

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        client = TestClient(app)

        # 1. Prepare Project and Experiment
        project = Project(id=uuid.uuid4(), name="E2E Synthetic Biology Project")
        experiment = Experiment(
            id=uuid.uuid4(),
            project_id=project.id,
            name="Metabolic Optimization Factorial Experiment",
            status="active",
            organism="Corynebacterium glutamicum",
            condition_type="Nutrient and Temperature Variations",
        )
        db_session.add_all([project, experiment])
        db_session.commit()

        # 2. Register conceptual factors and levels via API
        fa_payload = {
            "name": "Carbon Source Feedstock",
            "factor_type": "chemical",
            "description": "Primary carbon feed substrate",
            "levels": [
                {"name": "Glucose", "order_index": 1},
                {"name": "Glycerol", "order_index": 2},
            ],
        }
        res_fa = client.post(f"/api/v1/experiments/{experiment.id}/factors", json=fa_payload)
        assert res_fa.status_code == 201
        factor_a_data = res_fa.json()
        assert len(factor_a_data["levels"]) == 2

        fb_payload = {
            "name": "Culture Temperature",
            "factor_type": "physical",
            "description": "Incubation setpoint in degrees Celsius",
            "levels": [
                {"name": "30C", "order_index": 1},
                {"name": "37C", "order_index": 2},
            ],
        }
        res_fb = client.post(f"/api/v1/experiments/{experiment.id}/factors", json=fb_payload)
        assert res_fb.status_code == 201
        factor_b_data = res_fb.json()

        # 3. Prepare and link a 2x2 factorial dataset with replicates
        storage = LocalStorageService(base_dir=tmp_path / "datasets")
        csv_data = (
            "substrate,temperature,biomass_yield\n"
            "Glucose,30C,14.2\nGlucose,30C,14.5\nGlucose,30C,14.1\n"
            "Glucose,37C,18.6\nGlucose,37C,18.9\nGlucose,37C,18.4\n"
            "Glycerol,30C,11.0\nGlycerol,30C,11.3\nGlycerol,30C,11.1\n"
            "Glycerol,37C,21.5\nGlycerol,37C,22.0\nGlycerol,37C,21.8\n"
        )
        ds_id = uuid.uuid4()
        rel_path = storage.save_file(ds_id, "metabolic_data.csv", csv_data.encode("utf-8"))

        dataset = Dataset(
            id=ds_id,
            project_id=project.id,
            experiment_id=experiment.id,
            name="Metabolic Production Metrics",
            file_name="metabolic_data.csv",
            file_type="csv",
            file_size=len(csv_data),
            row_count=12,
            column_count=3,
            storage_path=rel_path,
        )
        db_session.add(dataset)
        experiment.dataset_id = dataset.id
        db_session.commit()

        # 4 & 5. Execute Factorial Analysis via REST API
        analysis_payload = {
            "name": "Carbon x Temperature Growth Screen",
            "description": "Full Two-Way factorial evaluation of substrate utilization across temperatures",
            "dataset_id": str(dataset.id),
            "factor_a_id": factor_a_data["id"],
            "factor_b_id": factor_b_data["id"],
            "factor_a_column": "substrate",
            "factor_b_column": "temperature",
            "measurement_column": "biomass_yield",
            "alpha": 0.05,
            "post_hoc_method": "tukey",
            "check_assumptions": True,
            "parameters": {},
        }
        res_exec = client.post(
            f"/api/v1/experiments/{experiment.id}/factorial-comparisons",
            json=analysis_payload,
        )
        assert res_exec.status_code == 201
        exec_data = res_exec.json()
        fcomp_id = exec_data["id"]
        analysis_id = exec_data["analysis_id"]

        # 6. Verify consistent persistence in ORM
        fcomp_orm = db_session.scalar(
            select(FactorialComparison).where(FactorialComparison.id == uuid.UUID(fcomp_id))
        )
        assert fcomp_orm is not None
        assert fcomp_orm.name == "Carbon x Temperature Growth Screen"
        assert fcomp_orm.status == "completed"

        analysis_orm = db_session.scalar(
            select(Analysis).where(Analysis.id == uuid.UUID(analysis_id))
        )
        assert analysis_orm is not None
        assert analysis_orm.analysis_type == "two_way_anova"

        # 7. Retrieve saved analysis via GET endpoint
        res_get = client.get(f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{fcomp_id}")
        assert res_get.status_code == 200
        get_data = res_get.json()
        assert get_data["id"] == fcomp_id
        res_summary = get_data["result_summary"]
        assert "effects" in res_summary
        assert "substrate" in res_summary["effects"]
        assert "temperature" in res_summary["effects"]
        assert "substrate × temperature" in res_summary["effects"]

        # 8. Generate structured JSON experiment report
        res_rep_json = client.get(f"/api/v1/experiments/{experiment.id}/report?format=json")
        assert res_rep_json.status_code == 200
        rep_data = res_rep_json.json()
        assert "factorial_analyses" in rep_data
        assert len(rep_data["factorial_analyses"]) == 1
        fa_rep = rep_data["factorial_analyses"][0]
        assert fa_rep["comparison_name"] == "Carbon x Temperature Growth Screen"
        assert fa_rep["factor_a_name"] == "Carbon Source Feedstock"
        assert fa_rep["factor_b_name"] == "Culture Temperature"
        assert fa_rep["measurement_column"] == "biomass_yield"
        assert len(fa_rep["effects"]) == 4

        # 9. Render and verify Markdown report
        res_rep_md = client.get(f"/api/v1/experiments/{experiment.id}/report?format=markdown")
        assert res_rep_md.status_code == 200
        md_text = res_rep_md.text
        assert "## 9. Two-Way Factorial Analyses" in md_text
        assert "Carbon x Temperature Growth Screen" in md_text
        assert "Type III ANOVA Table" in md_text
        assert "Model Assumption Diagnostics" in md_text
        assert "## 10. Provenance & Reproducibility" in md_text

        # 10 & 11. Verify Export Downloads
        res_exp_json = client.get(f"/api/v1/experiments/{experiment.id}/report/export?format=json")
        assert res_exp_json.status_code == 200
        assert "attachment" in res_exp_json.headers["content-disposition"]
        assert "application/json" in res_exp_json.headers["content-type"]

        res_exp_md = client.get(f"/api/v1/experiments/{experiment.id}/report/export?format=markdown")
        assert res_exp_md.status_code == 200
        assert "attachment" in res_exp_md.headers["content-disposition"]
        assert "text/markdown" in res_exp_md.headers["content-type"]

        # 12. Verify invalid run leaves no phantom records (Atomicity)
        initial_fcomp_count = len(db_session.scalars(select(FactorialComparison)).all())
        initial_analysis_count = len(db_session.scalars(select(Analysis)).all())

        bad_payload = {
            "name": "Invalid Factorial Comparison",
            "dataset_id": str(dataset.id),
            "factor_a_column": "nonexistent_col_a",
            "factor_b_column": "substrate",
            "measurement_column": "biomass_yield",
        }
        res_bad = client.post(
            f"/api/v1/experiments/{experiment.id}/factorial-comparisons",
            json=bad_payload,
        )
        assert res_bad.status_code == 400

        post_fcomp_count = len(db_session.scalars(select(FactorialComparison)).all())
        post_analysis_count = len(db_session.scalars(select(Analysis)).all())
        assert post_fcomp_count == initial_fcomp_count
        assert post_analysis_count == initial_analysis_count

        # 13. Verify deletion behavior
        res_del = client.delete(
            f"/api/v1/experiments/{experiment.id}/factorial-comparisons/{fcomp_id}"
        )
        assert res_del.status_code == 204
        deleted_fcomp = db_session.scalar(
            select(FactorialComparison).where(FactorialComparison.id == uuid.UUID(fcomp_id))
        )
        assert deleted_fcomp is None
    finally:
        app.dependency_overrides.pop(get_db, None)
