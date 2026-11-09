import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import ExperimentNotFoundError
from app.main import app
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_factor import ExperimentalFactor
from app.models.experimental_group import ExperimentalGroup
from app.models.factor_level import FactorLevel
from app.models.factorial_comparison import FactorialComparison
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


def test_generate_report_with_factorial_analysis_significant_interaction(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests generating a report with a saved FactorialComparison having a significant interaction."""
    # 1. Add Conceptual Factors & Levels
    factor_a = ExperimentalFactor(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        name="Promoter Strength",
        factor_type="genetic_part",
        description="Constitutive promoter variants",
    )
    factor_b = ExperimentalFactor(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        name="Inducer Concentration",
        factor_type="chemical",
        description="IPTG inducer concentrations in uM",
    )
    db_session.add_all([factor_a, factor_b])
    db_session.commit()

    lvl_a1 = FactorLevel(id=uuid.uuid4(), factor_id=factor_a.id, name="Low", order_index=1)
    lvl_a2 = FactorLevel(id=uuid.uuid4(), factor_id=factor_a.id, name="High", order_index=2)
    lvl_b1 = FactorLevel(id=uuid.uuid4(), factor_id=factor_b.id, name="0 uM", order_index=1)
    lvl_b2 = FactorLevel(id=uuid.uuid4(), factor_id=factor_b.id, name="100 uM", order_index=2)
    db_session.add_all([lvl_a1, lvl_a2, lvl_b1, lvl_b2])
    db_session.commit()

    # 2. Add Analysis & FactorialComparison
    analysis_record = Analysis(
        id=uuid.uuid4(),
        dataset_id=test_dataset.id,
        experiment_id=test_experiment.id,
        analysis_type="two_way_anova",
        parameters={
            "alpha": 0.05,
            "post_hoc_method": "tukey",
            "contrast_coding": "sum-to-zero (deviation)",
            "type_ss": 3,
        },
        result={
            "test_name": "Two-Way ANOVA (Type III SS)",
            "model_formula": "gfp_fluorescence ~ C(promoter, Sum) + C(inducer, Sum) + C(promoter, Sum):C(inducer, Sum)",
            "response_column": "gfp_fluorescence",
            "factor_a_column": "promoter",
            "factor_b_column": "inducer",
            "factor_a_levels": ["J23106", "J23100"],
            "factor_b_levels": ["0", "100"],
            "total_rows_input": 24,
            "valid_rows_used": 24,
            "excluded_rows_count": 0,
            "exclusion_reasons": {"missing_values": 0},
            "design_balance": "balanced",
            "is_balanced": True,
            "anova_type": "Type III",
            "contrast_coding": "sum-to-zero (deviation)",
            "cell_sample_sizes": {
                "J23106:0": 6,
                "J23106:100": 6,
                "J23100:0": 6,
                "J23100:100": 6,
            },
            "effects": {
                "factor_a": {
                    "effect_name": "Promoter Strength",
                    "df": 1.0,
                    "sum_sq": 120.50,
                    "mean_sq": 120.50,
                    "f_statistic": 18.25,
                    "p_value": 0.0003,
                    "is_significant": True,
                    "partial_eta_squared": 0.4771,
                    "partial_eta_squared_ci": [0.18, 0.65],
                    "effect_size_interpretation": "large",
                },
                "factor_b": {
                    "effect_name": "Inducer Concentration",
                    "df": 1.0,
                    "sum_sq": 85.20,
                    "mean_sq": 85.20,
                    "f_statistic": 12.91,
                    "p_value": 0.0018,
                    "is_significant": True,
                    "partial_eta_squared": 0.3923,
                    "partial_eta_squared_ci": [0.12, 0.58],
                    "effect_size_interpretation": "large",
                },
                "interaction": {
                    "effect_name": "Promoter Strength × Inducer Concentration",
                    "df": 1.0,
                    "sum_sq": 42.10,
                    "mean_sq": 42.10,
                    "f_statistic": 6.38,
                    "p_value": 0.0199,
                    "is_significant": True,
                    "partial_eta_squared": 0.2418,
                    "partial_eta_squared_ci": [0.03, 0.46],
                    "effect_size_interpretation": "large",
                },
                "residual": {
                    "effect_name": "Residual",
                    "df": 20.0,
                    "sum_sq": 132.00,
                    "mean_sq": 6.60,
                    "f_statistic": None,
                    "p_value": None,
                    "is_significant": False,
                    "partial_eta_squared": None,
                },
            },
            "interaction_significant": True,
            "post_hoc_method": "tukey",
            "simple_effects": [
                {
                    "slice_factor": "Promoter Strength",
                    "slice_level": "J23100",
                    "target_factor": "Inducer Concentration",
                    "df_between": 1.0,
                    "df_within": 20.0,
                    "f_statistic": 16.50,
                    "p_value": 0.0006,
                    "is_significant": True,
                    "pairwise_comparisons": [],
                }
            ],
            "assumptions": [
                {
                    "test_name": "Shapiro-Wilk Normality of Residuals",
                    "statistic": 0.965,
                    "p_value": 0.54,
                    "is_valid": True,
                    "warning_message": None,
                },
                {
                    "test_name": "Levene Test for Homogeneity of Variance",
                    "statistic": 1.12,
                    "p_value": 0.36,
                    "is_valid": True,
                    "warning_message": None,
                },
            ],
            "warnings": ["Observational caveat: Check biological replicates."],
            "scientific_statement": (
                "Type III Two-Way ANOVA revealed statistically significant main effects and interaction. "
                "Simple main effects decomposition confirms differential induction across promoter variants."
            ),
        },
        software_version="0.1.0",
    )
    db_session.add(analysis_record)
    db_session.flush()

    fcomp = FactorialComparison(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        analysis_id=analysis_record.id,
        dataset_id=test_dataset.id,
        name="Promoter x Inducer Factorial Screen",
        description="Evaluating transcriptional output under varying genetic and chemical inputs",
        status="completed",
        factor_a_id=factor_a.id,
        factor_b_id=factor_b.id,
        factor_a_column="promoter",
        factor_b_column="inducer",
        measurement_column="gfp_fluorescence",
        parameters={
            "alpha": 0.05,
            "post_hoc_method": "tukey",
            "contrast_coding": "sum-to-zero (deviation)",
            "type_ss": 3,
        },
        result_summary=analysis_record.result,
    )
    db_session.add(fcomp)
    db_session.commit()

    service = ExperimentReportService(db_session)
    report = service.generate_report(test_experiment.id)

    # Verify Report DTO structure
    assert len(report.factorial_analyses) == 1
    fa = report.factorial_analyses[0]
    assert fa.comparison_id == fcomp.id
    assert fa.analysis_id == analysis_record.id
    assert fa.comparison_name == "Promoter x Inducer Factorial Screen"
    assert fa.dataset_id == test_dataset.id
    assert fa.dataset_name == test_dataset.name
    assert fa.factor_a_name == "Promoter Strength"
    assert fa.factor_a_column == "promoter"
    assert fa.factor_b_name == "Inducer Concentration"
    assert fa.factor_b_column == "inducer"
    assert fa.measurement_column == "gfp_fluorescence"
    assert fa.interaction_significant is True
    assert fa.design_balance == "balanced"
    assert fa.valid_rows_used == 24
    assert len(fa.effects) == 4
    assert len(fa.simple_effects) == 1
    assert len(fa.assumptions) == 2
    assert len(fa.warnings) == 1
    assert "Type III Two-Way ANOVA" in (fa.scientific_statement or "")

    # Verify Provenance
    prov_fcomp = [p for p in report.provenance if p.section == "factorial_analyses"]
    assert len(prov_fcomp) == 1
    assert prov_fcomp[0].comparison_id == fcomp.id
    assert prov_fcomp[0].analysis_id == analysis_record.id

    # Verify Markdown Output
    md = service.render_markdown(report)
    assert "## 9. Two-Way Factorial Analyses" in md
    assert "Promoter x Inducer Factorial Screen" in md
    assert "Type III ANOVA Table" in md
    assert "Significant Interaction Detected" in md
    assert "Conditional simple main effects" in md
    assert "Model Assumption Diagnostics" in md
    assert "Factorial Design Cell Sample Sizes" in md
    assert "Scientific Statement" in md
    assert "## 10. Provenance & Reproducibility" in md
    assert "## 11. Appendix & Limitations" in md


def test_generate_report_with_factorial_analysis_non_significant_interaction(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests generating a report when interaction is not significant and marginal post-hocs are reported."""
    fcomp = FactorialComparison(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        dataset_id=test_dataset.id,
        name="Additive Factorial Test",
        status="completed",
        factor_a_column="carbon_source",
        factor_b_column="temp_c",
        measurement_column="biomass_yield",
        parameters={"alpha": 0.05, "post_hoc_method": "bonferroni"},
        result_summary={
            "test_name": "Two-Way ANOVA (Type III SS)",
            "response_column": "biomass_yield",
            "factor_a_column": "carbon_source",
            "factor_b_column": "temp_c",
            "interaction_significant": False,
            "post_hoc_method": "bonferroni",
            "effects": {
                "factor_a": {
                    "effect_name": "carbon_source",
                    "df": 2.0,
                    "sum_sq": 50.0,
                    "mean_sq": 25.0,
                    "f_statistic": 5.0,
                    "p_value": 0.015,
                    "is_significant": True,
                    "partial_eta_squared": 0.25,
                },
                "interaction": {
                    "effect_name": "carbon_source × temp_c",
                    "df": 2.0,
                    "sum_sq": 4.0,
                    "mean_sq": 2.0,
                    "f_statistic": 0.40,
                    "p_value": 0.675,
                    "is_significant": False,
                    "partial_eta_squared": 0.02,
                },
            },
            "post_hoc_comparisons": [
                {
                    "factor": "carbon_source",
                    "group1": "Glucose",
                    "group2": "Glycerol",
                    "mean_difference": 1.25,
                    "p_value_adjusted": 0.018,
                    "ci_95": [0.25, 2.25],
                    "is_significant": True,
                }
            ],
            "assumptions": [],
            "warnings": [],
            "scientific_statement": "No significant interaction was observed.",
        },
    )
    db_session.add(fcomp)
    db_session.commit()

    service = ExperimentReportService(db_session)
    report = service.generate_report(test_experiment.id)

    assert len(report.factorial_analyses) >= 1
    target_fa = next(fa for fa in report.factorial_analyses if fa.comparison_id == fcomp.id)
    assert target_fa.interaction_significant is False
    assert len(target_fa.post_hoc_comparisons) == 1

    md = service.render_markdown(report)
    assert "No Significant Interaction" in md
    assert "Marginal Post-Hoc Pairwise Comparisons" in md
    assert "Glucose vs Glycerol" in md


def test_generate_report_with_sparse_factorial_analysis(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests that missing optional fields in saved factorial comparisons do not break report generation."""
    fcomp = FactorialComparison(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        dataset_id=test_dataset.id,
        name="Sparse Analysis Test",
        status="completed",
        factor_a_column="factor1",
        factor_b_column="factor2",
        measurement_column="response",
        parameters={},
        result_summary={},  # completely empty result dict
    )
    db_session.add(fcomp)
    db_session.commit()

    service = ExperimentReportService(db_session)
    report = service.generate_report(test_experiment.id)

    target_fa = next(fa for fa in report.factorial_analyses if fa.comparison_id == fcomp.id)
    assert target_fa.comparison_name == "Sparse Analysis Test"
    assert target_fa.effects == []
    assert target_fa.interaction_significant is False

    md = service.render_markdown(report)
    assert "Sparse Analysis Test" in md
    assert "No effect results available." in md


def test_factorial_analysis_experiment_isolation(
    db_session: Session, test_project: Project, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Verifies that factorial analyses belonging to Experiment B never appear in Experiment A's report."""
    exp_b = Experiment(
        id=uuid.uuid4(),
        project_id=test_project.id,
        name="Experiment B Isolated",
        status="active",
    )
    fcomp_b = FactorialComparison(
        id=uuid.uuid4(),
        experiment_id=exp_b.id,
        name="Experiment B Factorial Analysis",
        status="completed",
        factor_a_column="col_a",
        factor_b_column="col_b",
        measurement_column="val",
        result_summary={"test_name": "Two-Way ANOVA"},
    )
    db_session.add_all([exp_b, fcomp_b])
    db_session.commit()

    service = ExperimentReportService(db_session)
    report_a = service.generate_report(test_experiment.id)

    fa_ids_a = [fa.comparison_id for fa in report_a.factorial_analyses]
    assert fcomp_b.id not in fa_ids_a

    report_b = service.generate_report(exp_b.id)
    fa_ids_b = [fa.comparison_id for fa in report_b.factorial_analyses]
    assert fcomp_b.id in fa_ids_b


def test_report_api_endpoints_with_factorial_analysis(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
) -> None:
    """Tests GET /report and /report/export endpoints returning factorial analysis in JSON and Markdown formats."""
    fcomp = FactorialComparison(
        id=uuid.uuid4(),
        experiment_id=test_experiment.id,
        dataset_id=test_dataset.id,
        name="API Export Factorial Analysis",
        status="completed",
        factor_a_column="promoter",
        factor_b_column="inducer",
        measurement_column="output",
        parameters={"alpha": 0.05, "post_hoc_method": "tukey"},
        result_summary={
            "test_name": "Two-Way ANOVA (Type III SS)",
            "effects": {
                "factor_a": {
                    "effect_name": "promoter",
                    "df": 1.0,
                    "sum_sq": 10.0,
                    "mean_sq": 10.0,
                    "f_statistic": 5.0,
                    "p_value": 0.03,
                    "is_significant": True,
                    "partial_eta_squared": 0.20,
                }
            },
            "scientific_statement": "API Export Verification Statement.",
        },
    )
    db_session.add(fcomp)
    db_session.commit()

    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        test_client = TestClient(app)

        # 1. JSON Report Endpoint
        res_json = test_client.get(f"/api/v1/experiments/{test_experiment.id}/report?format=json")
        assert res_json.status_code == 200
        data = res_json.json()
        assert "factorial_analyses" in data
        assert len(data["factorial_analyses"]) >= 1
        found = any(fa["comparison_name"] == "API Export Factorial Analysis" for fa in data["factorial_analyses"])
        assert found is True

        # 2. Markdown Report Endpoint
        res_md = test_client.get(f"/api/v1/experiments/{test_experiment.id}/report?format=markdown")
        assert res_md.status_code == 200
        assert "text/markdown" in res_md.headers.get("content-type", "")
        assert "## 9. Two-Way Factorial Analyses" in res_md.text
        assert "API Export Factorial Analysis" in res_md.text

        # 3. Export JSON Download Endpoint
        res_exp_json = test_client.get(f"/api/v1/experiments/{test_experiment.id}/report/export?format=json")
        assert res_exp_json.status_code == 200
        assert "application/json" in res_exp_json.headers.get("content-type", "")
        assert "attachment" in res_exp_json.headers.get("content-disposition", "")
        assert "API Export Factorial Analysis" in res_exp_json.text

        # 4. Export Markdown Download Endpoint
        res_exp_md = test_client.get(f"/api/v1/experiments/{test_experiment.id}/report/export?format=markdown")
        assert res_exp_md.status_code == 200
        assert "text/markdown" in res_exp_md.headers.get("content-type", "")
        assert "attachment" in res_exp_md.headers.get("content-disposition", "")
        assert "## 9. Two-Way Factorial Analyses" in res_exp_md.text
    finally:
        app.dependency_overrides.pop(get_db, None)

