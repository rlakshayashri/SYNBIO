import uuid
from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.models.project import Project
from app.models.replicate import Replicate
from app.schemas.report import ExperimentReport
from app.services.experiment_report_service import ExperimentReportService


@pytest.fixture
def test_project(db_session: Session) -> Generator[Project, None, None]:
    proj = Project(
        id=uuid.uuid4(),
        name="Report Test Project",
        description="Project for testing scientific report generation",
    )
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)
    yield proj


@pytest.fixture
def test_experiment(db_session: Session, test_project: Project) -> Generator[Experiment, None, None]:
    exp = Experiment(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="CRISPR Target Gene Knockout Experiment",
        description="Assessing expression levels across wildtype and knockout lines.",
        status="active",
        objective="Determine target gene knockout efficiency via qPCR assay.",
        organism="Escherichia coli K-12",
        condition_type="Gene Knockout",
        notes="Replicates prepared under standard 37C growth conditions.",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    # Add Experimental Groups & Replicates
    group1 = ExperimentalGroup(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        name="Control Group",
        group_code="WT",
        is_control=True,
        description="Wildtype untreated control",
    )
    group2 = ExperimentalGroup(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        name="Knockout Group",
        group_code="KO",
        is_control=False,
        description="Target gene knockout strain",
    )
    db_session.add_all([group1, group2])
    db_session.commit()

    rep1 = Replicate(
        id=uuid.uuid4(),
        group_id=group1.id,
        replicate_name="WT_BioRep_1",
        sample_identifier="S01",
        replicate_type="biological",
    )
    rep2 = Replicate(
        id=uuid.uuid4(),
        group_id=group2.id,
        replicate_name="KO_BioRep_1",
        sample_identifier="S02",
        replicate_type="biological",
    )
    db_session.add_all([rep1, rep2])
    db_session.commit()
    db_session.refresh(exp)
    yield exp


@pytest.fixture
def test_dataset(
    db_session: Session, test_project: Project, test_experiment: Experiment
) -> Generator[Dataset, None, None]:
    ds = Dataset(
        id=uuid.uuid4(),
        project_id=test_project.id,
        experiment_id=test_experiment.id,
        name="Expression Metrics Dataset",
        file_name="expression_data.csv",
        file_type="csv",
        file_size=2048,
        row_count=100,
        column_count=5,
        storage_path="datasets/expression_data.csv",
    )
    db_session.add(ds)
    test_experiment.dataset_id = ds.id
    db_session.commit()
    db_session.refresh(ds)
    yield ds


def test_generate_report_complete_flow(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests generating a complete report with validation, statistics, and group comparison analyses."""
    # Add validation Analysis
    val_analysis = Analysis(
        id=uuid.uuid4(),
        dataset_id=test_dataset.id,
        experiment_id=test_experiment.id,
        analysis_type="validation",
        parameters={},
        result={
            "summary": {"is_valid": True},
            "missing_values": {"missing_count": 0},
            "duplicate_rows": {"duplicate_count": 0},
            "data_types": {"column_types": {"expression": "float64"}},
            "empty_columns": {"empty_columns": []},
            "outliers": {"outlier_counts": {"expression": 1}},
        },
        software_version="0.1.0",
    )

    # Add descriptive statistics Analysis
    stats_analysis = Analysis(
        id=uuid.uuid4(),
        dataset_id=test_dataset.id,
        experiment_id=test_experiment.id,
        analysis_type="descriptive_statistics",
        parameters={},
        result={
            "statistics": {
                "expression": {
                    "count": 100,
                    "missing_count": 0,
                    "mean": 12.456,
                    "std": 1.234,
                    "median": 12.300,
                    "min": 9.500,
                    "max": 15.100,
                    "iqr": 1.800,
                }
            }
        },
        software_version="0.1.0",
    )

    # Add statistical comparison Analysis & Comparison record
    comp_analysis = Analysis(
        id=uuid.uuid4(),
        dataset_id=test_dataset.id,
        experiment_id=test_experiment.id,
        analysis_type="experimental_comparison_two_group_welch_ttest",
        parameters={"method": "welch_ttest"},
        result={
            "statistical_result": {
                "test_name": "Welch Two-Sample t-test",
                "statistic_name": "t-statistic",
                "statistic_value": -4.5123,
                "p_value": 0.00012,
                "degrees_of_freedom": 18.45,
                "effect_size_name": "Cohen's d",
                "effect_size_value": 1.45,
                "confidence_interval": [-3.5, -1.2],
                "is_significant": True,
            }
        },
        software_version="0.1.0",
    )
    comp_record = Comparison(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        analysis_id=comp_analysis.id,
        name="WT vs KO Expression Comparison",
        comparison_type="two_group",
        measurement_column="expression",
        group_column="group",
        parameters={"method": "welch_ttest"},
        result_summary=comp_analysis.result,
    )

    db_session.add_all([val_analysis, stats_analysis, comp_analysis, comp_record])
    db_session.commit()

    service = ExperimentReportService(db_session)
    report: ExperimentReport = service.generate_report(test_experiment.id)

    # 1. Verify Header & Context
    assert report.metadata.experiment_id == test_experiment.id
    assert report.metadata.experiment_name == test_experiment.name
    assert report.experimental_context.organism == "Escherichia coli K-12"
    assert len(report.experimental_context.groups) == 2

    # 2. Verify Datasets
    assert len(report.datasets) == 1
    assert report.datasets[0].dataset_id == test_dataset.id
    assert report.datasets[0].has_validation is True

    # 3. Verify Validation
    assert len(report.data_quality) == 1
    assert report.data_quality[0].validation_passed is True

    # 4. Verify Descriptive Statistics (numeric values preserved exactly)
    assert len(report.descriptive_statistics) == 1
    ds_item = report.descriptive_statistics[0]
    assert ds_item.column_name == "expression"
    assert ds_item.mean == 12.456
    assert ds_item.std_dev == 1.234

    # 5. Verify Statistical Results (scientific accuracy preserved)
    assert len(report.statistical_results) == 1
    stat_item = report.statistical_results[0]
    assert stat_item.statistic_value == -4.5123
    assert stat_item.p_value == 0.00012
    assert stat_item.is_significant is True
    assert stat_item.confidence_interval == [-3.5, -1.2]

    # 6. Verify Provenance Traceability Links
    assert len(report.provenance) >= 3
    prov_sections = [p.section for p in report.provenance]
    assert "data_quality" in prov_sections
    assert "descriptive_statistics" in prov_sections
    assert "statistical_results" in prov_sections

    # 7. Verify Markdown Rendering
    md = service.render_markdown(report)
    assert "# Scientific Report: CRISPR Target Gene Knockout Experiment" in md
    assert "## 1. Experiment Overview" in md
    assert "## 4. Data Quality / Validation" in md
    assert "## 8. Statistical Results" in md
    assert "SynDataX reports recorded experimental evidence" in md


def test_generate_report_empty_experiment(
    db_session: Session, test_experiment: Experiment
) -> None:
    """Tests report generation for an experiment with no attached datasets or analyses."""
    service = ExperimentReportService(db_session)
    report = service.generate_report(test_experiment.id)

    assert report.metadata.experiment_id == test_experiment.id
    assert len(report.datasets) == 0
    assert len(report.data_quality) == 0
    assert len(report.descriptive_statistics) == 0
    assert len(report.statistical_results) == 0

    md = service.render_markdown(report)
    assert "No datasets are attached to this experiment." in md
    assert "No validation or data quality analyses have been recorded yet." in md
    assert "No statistical test results recorded for this experiment." in md


def test_generate_report_nonexistent_experiment_raises(db_session: Session) -> None:
    """Tests that generating a report for a missing experiment ID raises ExperimentNotFoundError."""
    service = ExperimentReportService(db_session)
    fake_id = uuid.uuid4()
    with pytest.raises(ExperimentNotFoundError):
        service.generate_report(fake_id)


def test_generate_report_isolation(
    db_session: Session, test_project: Project, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests that Experiment A's report never includes Experiment B's analyses or datasets."""
    # Create Experiment B
    exp_b = Experiment(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="Experiment B Independent Test",
        status="active",
    )
    ds_b = Dataset(
        id=uuid.uuid4(),
        project_id=test_project.id,
        experiment_id=exp_b.id,
        name="Dataset B",
        file_name="ds_b.csv",
        file_type="csv",
        file_size=500,
        storage_path="ds_b.csv",
    )
    analysis_b = Analysis(
        id=uuid.uuid4(),
        dataset_id=ds_b.id,
        experiment_id=exp_b.id,
        analysis_type="validation",
        result={"summary": {"is_valid": True}},
    )
    db_session.add_all([exp_b, ds_b, analysis_b])
    db_session.commit()

    service = ExperimentReportService(db_session)
    report_a = service.generate_report(test_experiment.id)

    dataset_ids_a = [d.dataset_id for d in report_a.datasets]
    assert ds_b.id not in dataset_ids_a

    analysis_ids_a = [dq.analysis_id for dq in report_a.data_quality]
    assert analysis_b.id not in analysis_ids_a
