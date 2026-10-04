from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.comparison import ComparisonCreateRequest
from app.schemas.experiment import ExperimentCreate
from app.schemas.experimental_group import ExperimentalGroupCreate
from app.services.comparison_service import ComparisonService
from app.services.experiment_dataset_service import ExperimentDatasetService
from app.services.experiment_results_service import ExperimentResultsService
from app.services.experiment_service import ExperimentService
from app.services.group_service import GroupService
from app.services.statistics_service import StatisticsService
from app.services.validation_service import ValidationService


def test_experiment_results_aggregation_and_provenance(db_session: Session, tmp_path):
    # 1. Setup Project & Experiment
    project = Project(name="Results Test Project", description="Test project for Phase 3D")
    db_session.add(project)
    db_session.commit()

    exp_service = ExperimentService(db_session)
    experiment = exp_service.create(
        ExperimentCreate(
            project_id=project.id,
            name="E. coli Growth Experiment",
            objective="Quantify growth rate across temperature conditions",
        )
    )

    # 2. Add Experimental Groups
    group_service = GroupService(db_session)
    g_a = group_service.create(
        experiment.id,
        ExperimentalGroupCreate(name="WT Control", group_code="CTRL", is_control=True),
    )
    g_b = group_service.create(
        experiment.id,
        ExperimentalGroupCreate(name="Knockout Mutant", group_code="TRT", is_control=False),
    )

    # 3. Upload & Attach Dataset
    csv_bytes = (
        b"sample_id,condition,OD600\n"
        b"S1,CTRL,0.45\n"
        b"S2,CTRL,0.48\n"
        b"S3,CTRL,0.44\n"
        b"S4,TRT,0.85\n"
        b"S5,TRT,0.88\n"
        b"S6,TRT,0.82\n"
    )
    exp_ds_service = ExperimentDatasetService(db_session)
    dataset = exp_ds_service.upload_and_attach(
        experiment_id=experiment.id,
        file_name="plate_reader_data.csv",
        file_type="csv",
        file_bytes=csv_bytes,
        name="Growth Measurements CSV",
    )

    # 4. Execute Validation, Statistics, and Comparison
    val_service = ValidationService(db_session)
    val_service.run_validation(dataset.id)

    stats_service = StatisticsService(db_session)
    stats_service.run_descriptive_statistics(dataset.id)

    comp_service = ComparisonService(db_session)
    comp_req = ComparisonCreateRequest(
        name="CTRL vs TRT OD600 Comparison",
        comparison_type="two_group",
        group_a_id=g_a.id,
        group_b_id=g_b.id,
        measurement_column="OD600",
        group_column="condition",
        method="welch_ttest",
        alpha=0.05,
    )
    comp_service.run_comparison(experiment.id, comp_req)

    # 5. Execute ExperimentResultsService
    results_service = ExperimentResultsService(db_session)
    res_payload = results_service.get_results(experiment.id)

    # 6. Verify Results Aggregation & Provenance
    assert res_payload.experiment_id == experiment.id
    assert res_payload.experiment_name == "E. coli Growth Experiment"
    assert res_payload.total_results >= 3  # Validation, Stats, Comparison

    # Check comparison result item
    comp_item = next(
        r for r in res_payload.results if "experimental_comparison" in r.analysis_type
    )
    assert comp_item.provenance.experiment_id == experiment.id
    assert comp_item.provenance.dataset_id == dataset.id
    assert comp_item.comparison is not None
    assert comp_item.comparison.group_a_name == "WT Control"
    assert comp_item.comparison.group_b_name == "Knockout Mutant"
    assert comp_item.comparison.measurement_column == "OD600"
    assert "statistical_result" in comp_item.result

    # 7. Verify Exports
    csv_str = results_service.export_csv(experiment.id)
    assert "analysis_id,analysis_type,created_at" in csv_str
    assert "OD600" in csv_str
    assert "WT Control" in csv_str
