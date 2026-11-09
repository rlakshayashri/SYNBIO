import uuid
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_factor import ExperimentalFactor
from app.models.factor_level import FactorLevel
from app.models.factorial_comparison import FactorialComparison
from app.models.project import Project
from app.schemas.factor import (
    ExperimentalFactorResponse,
    FactorLevelResponse,
)
from app.schemas.factorial_comparison import (
    FactorialComparisonResponse,
)
from app.storage.local import LocalStorageService


@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="M9 Phase 1 Project", description="Testing factorial domain models")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_experiment(db_session: Session, test_project: Project) -> Experiment:
    experiment = Experiment(
        project_id=test_project.id,
        name="CRISPR-Factorial-Optimization",
        status="in_progress",
        objective="Assess temperature and promoter dosage interactions",
    )
    db_session.add(experiment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture
def test_dataset(db_session: Session, test_project: Project, test_experiment: Experiment, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"temp,iptg,yield\n30,50,150.2\n30,250,300.5\n37,50,210.0\n37,250,520.1\n"
    rel_path = storage.save_file(dataset_id, "factorial_data.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        experiment_id=test_experiment.id,
        name="Factorial Expression Data",
        file_name="factorial_data.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=4,
        column_count=3,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


# --- 1. ExperimentalFactor Tests ---


def test_create_experimental_factor_success(db_session: Session, test_experiment: Experiment):
    """Verify factor creation with ownership link to experiment."""
    factor = ExperimentalFactor(
        experiment_id=test_experiment.id,
        name="Temperature",
        description="Incubation temperature shift",
        factor_type="environmental",
    )
    db_session.add(factor)
    db_session.commit()
    db_session.refresh(factor)

    assert factor.id is not None
    assert factor.name == "Temperature"
    assert factor.experiment_id == test_experiment.id
    assert factor.experiment.id == test_experiment.id
    assert factor in test_experiment.factors


def test_experimental_factor_name_uniqueness_within_experiment(db_session: Session, test_experiment: Experiment):
    """Verify that duplicate factor names within the same experiment are rejected."""
    f1 = ExperimentalFactor(experiment_id=test_experiment.id, name="IPTG_Concentration")
    db_session.add(f1)
    db_session.commit()

    f2 = ExperimentalFactor(experiment_id=test_experiment.id, name="IPTG_Concentration")
    db_session.add(f2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_experimental_factor_same_name_across_different_experiments_allowed(
    db_session: Session, test_project: Project, test_experiment: Experiment
):
    """Verify that identical factor names across separate experiments are valid."""
    exp2 = Experiment(project_id=test_project.id, name="Second Independent Exp")
    db_session.add(exp2)
    db_session.commit()

    f1 = ExperimentalFactor(experiment_id=test_experiment.id, name="Media_Type")
    f2 = ExperimentalFactor(experiment_id=exp2.id, name="Media_Type")
    db_session.add_all([f1, f2])
    db_session.commit()

    assert f1.id != f2.id
    assert f1.name == f2.name


# --- 2. FactorLevel Tests ---


def test_create_factor_levels_and_ordering(db_session: Session, test_experiment: Experiment):
    """Verify factor level creation, ownership by factor, and ordered retrieval."""
    factor = ExperimentalFactor(experiment_id=test_experiment.id, name="Dosage")
    db_session.add(factor)
    db_session.commit()

    lvl_high = FactorLevel(factor_id=factor.id, name="High", order_index=2)
    lvl_low = FactorLevel(factor_id=factor.id, name="Low", order_index=0)
    lvl_med = FactorLevel(factor_id=factor.id, name="Medium", order_index=1)
    db_session.add_all([lvl_high, lvl_low, lvl_med])
    db_session.commit()

    db_session.refresh(factor)
    assert len(factor.levels) == 3
    # Verify order_by="FactorLevel.order_index"
    assert [lvl.name for lvl in factor.levels] == ["Low", "Medium", "High"]


def test_factor_level_uniqueness_within_factor(db_session: Session, test_experiment: Experiment):
    """Verify duplicate level names within the same factor are rejected."""
    factor = ExperimentalFactor(experiment_id=test_experiment.id, name="Carbon_Source")
    db_session.add(factor)
    db_session.commit()

    lvl1 = FactorLevel(factor_id=factor.id, name="Glucose")
    db_session.add(lvl1)
    db_session.commit()

    lvl2 = FactorLevel(factor_id=factor.id, name="Glucose")
    db_session.add(lvl2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_factor_level_same_name_across_different_factors_allowed(db_session: Session, test_experiment: Experiment):
    """Verify that identical level names across distinct factors are valid."""
    f1 = ExperimentalFactor(experiment_id=test_experiment.id, name="Factor 1")
    f2 = ExperimentalFactor(experiment_id=test_experiment.id, name="Factor 2")
    db_session.add_all([f1, f2])
    db_session.commit()

    lvl1 = FactorLevel(factor_id=f1.id, name="Control")
    lvl2 = FactorLevel(factor_id=f2.id, name="Control")
    db_session.add_all([lvl1, lvl2])
    db_session.commit()

    assert lvl1.id != lvl2.id
    assert lvl1.name == lvl2.name


# --- 3. Cascade Deletion Tests ---


def test_factor_cascade_deletes_levels(db_session: Session, test_experiment: Experiment):
    """Verify deleting an ExperimentalFactor cascade-deletes all its FactorLevels."""
    factor = ExperimentalFactor(experiment_id=test_experiment.id, name="Nitrogen")
    db_session.add(factor)
    db_session.commit()

    lvl = FactorLevel(factor_id=factor.id, name="Ammonium")
    db_session.add(lvl)
    db_session.commit()
    lvl_id = lvl.id

    db_session.delete(factor)
    db_session.commit()

    assert db_session.get(FactorLevel, lvl_id) is None


def test_experiment_cascade_deletes_factors_and_factorial_comparisons(
    db_session: Session, test_project: Project, test_dataset: Dataset
):
    """Verify deleting an Experiment cascade-deletes its factors and factorial comparisons."""
    exp = Experiment(project_id=test_project.id, name="To Delete Exp")
    db_session.add(exp)
    db_session.commit()

    factor = ExperimentalFactor(experiment_id=exp.id, name="pH")
    db_session.add(factor)
    db_session.commit()
    factor_id = factor.id

    fcomp = FactorialComparison(
        experiment_id=exp.id,
        name="pH vs Temp",
        factor_a_column="pH",
        factor_b_column="temp",
        measurement_column="yield",
    )
    db_session.add(fcomp)
    db_session.commit()
    fcomp_id = fcomp.id

    db_session.delete(exp)
    db_session.commit()

    assert db_session.get(ExperimentalFactor, factor_id) is None
    assert db_session.get(FactorialComparison, fcomp_id) is None


# --- 4. FactorialComparison Tests ---


def test_create_factorial_comparison_valid_flow(
    db_session: Session, test_experiment: Experiment, test_dataset: Dataset
):
    """Verify full FactorialComparison creation with registered factors, dataset, and analysis."""
    f_temp = ExperimentalFactor(experiment_id=test_experiment.id, name="Temperature")
    f_iptg = ExperimentalFactor(experiment_id=test_experiment.id, name="IPTG")
    db_session.add_all([f_temp, f_iptg])
    db_session.commit()

    analysis = Analysis(
        dataset_id=test_dataset.id,
        experiment_id=test_experiment.id,
        analysis_type="two_way_anova",
        parameters={"factor_a": "temp", "factor_b": "iptg"},
        result={"f_stat_interaction": 12.4, "p_value_interaction": 0.0012},
    )
    db_session.add(analysis)
    db_session.commit()

    fcomp = FactorialComparison(
        experiment_id=test_experiment.id,
        analysis_id=analysis.id,
        dataset_id=test_dataset.id,
        name="Temperature x IPTG Interaction",
        status="completed",
        factor_a_id=f_temp.id,
        factor_b_id=f_iptg.id,
        factor_a_column="temp",
        factor_b_column="iptg",
        measurement_column="yield",
        parameters={"alpha": 0.05, "type": "III"},
        result_summary={"significant_interaction": True},
    )
    db_session.add(fcomp)
    db_session.commit()
    db_session.refresh(fcomp)

    assert fcomp.id is not None
    assert fcomp.experiment_id == test_experiment.id
    assert fcomp.dataset_id == test_dataset.id
    assert fcomp.factor_a.name == "Temperature"
    assert fcomp.factor_b.name == "IPTG"
    assert fcomp.analysis.id == analysis.id
    assert analysis.factorial_comparison.id == fcomp.id
    assert fcomp in test_experiment.factorial_comparisons

    # Validate ownership passes
    fcomp.validate_factor_ownership()


def test_factorial_comparison_distinct_factors_constraint(
    db_session: Session, test_experiment: Experiment
):
    """Verify database check constraint rejecting identical Factor A and Factor B IDs."""
    factor = ExperimentalFactor(experiment_id=test_experiment.id, name="SharedFactor")
    db_session.add(factor)
    db_session.commit()

    fcomp = FactorialComparison(
        experiment_id=test_experiment.id,
        name="Invalid Self Comparison",
        factor_a_id=factor.id,
        factor_b_id=factor.id,
        factor_a_column="col1",
        factor_b_column="col1",
        measurement_column="yield",
    )
    db_session.add(fcomp)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_factorial_comparison_cross_experiment_factor_validation(
    db_session: Session, test_project: Project, test_experiment: Experiment
):
    """Verify domain ownership validation when Factor A belongs to an unrelated experiment."""
    unrelated_exp = Experiment(project_id=test_project.id, name="Unrelated Exp")
    db_session.add(unrelated_exp)
    db_session.commit()

    foreign_factor = ExperimentalFactor(experiment_id=unrelated_exp.id, name="ForeignFactor")
    local_factor = ExperimentalFactor(experiment_id=test_experiment.id, name="LocalFactor")
    db_session.add_all([foreign_factor, local_factor])
    db_session.commit()

    fcomp = FactorialComparison(
        experiment_id=test_experiment.id,
        name="Cross Experiment Factor Test",
        factor_a_id=foreign_factor.id,
        factor_b_id=local_factor.id,
        factor_a_column="foreign",
        factor_b_column="local",
        measurement_column="yield",
    )
    db_session.add(fcomp)
    db_session.commit()

    with pytest.raises(ValueError, match="belongs to experiment"):
        fcomp.validate_factor_ownership()


# --- 5. Pydantic Schema Serialization Tests ---


def test_schema_serialization_from_orm(db_session: Session, test_experiment: Experiment):
    """Verify Pydantic schemas correctly serialize from ORM models."""
    factor = ExperimentalFactor(
        experiment_id=test_experiment.id,
        name="Oxygenation",
        description="Dissolved oxygen percentage",
        factor_type="environmental",
    )
    db_session.add(factor)
    db_session.commit()

    lvl = FactorLevel(factor_id=factor.id, name="20% DO", order_index=1)
    db_session.add(lvl)
    db_session.commit()
    db_session.refresh(factor)

    # Validate FactorLevelResponse
    lvl_resp = FactorLevelResponse.model_validate(lvl)
    assert lvl_resp.name == "20% DO"
    assert lvl_resp.order_index == 1

    # Validate ExperimentalFactorResponse
    factor_resp = ExperimentalFactorResponse.model_validate(factor)
    assert factor_resp.name == "Oxygenation"
    assert len(factor_resp.levels) == 1
    assert factor_resp.levels[0].name == "20% DO"

    # Validate FactorialComparisonResponse
    fcomp = FactorialComparison(
        experiment_id=test_experiment.id,
        name="O2 x Sugar",
        status="completed",
        factor_a_column="o2",
        factor_b_column="sugar",
        measurement_column="growth_rate",
        parameters={"alpha": 0.01},
        result_summary={"p_val": 0.003},
    )
    db_session.add(fcomp)
    db_session.commit()
    db_session.refresh(fcomp)

    fcomp_resp = FactorialComparisonResponse.model_validate(fcomp)
    assert fcomp_resp.name == "O2 x Sugar"
    assert fcomp_resp.status == "completed"
    assert fcomp_resp.parameters["alpha"] == 0.01
