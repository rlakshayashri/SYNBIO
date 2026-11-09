import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DatasetNotFoundError,
    ExperimentNotFoundError,
    ScientificValidationError,
)
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_factor import ExperimentalFactor
from app.models.factorial_comparison import FactorialComparison
from app.models.project import Project
from app.schemas.factor import ExperimentalFactorCreate, FactorLevelCreate
from app.schemas.factorial_comparison import (
    FactorialComparisonCreate,
    FactorialComparisonUpdate,
)
from app.scientific.statistics.models import PostHocMethod
from app.services.factor_service import FactorService
from app.services.factorial_analysis_service import FactorialAnalysisService
from app.storage.local import LocalStorageService


@pytest.fixture
def project(db_session: Session) -> Project:
    p = Project(name="Factorial Service Project", description="Testing factorial analysis service")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def experiment(db_session: Session, project: Project) -> Experiment:
    exp = Experiment(
        project_id=project.id,
        name="Strain x Temp Assay",
        status="active",
        objective="Analyze strain and temperature interaction effects",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def other_experiment(db_session: Session, project: Project) -> Experiment:
    exp = Experiment(
        project_id=project.id,
        name="Other Unrelated Experiment",
        status="draft",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture
def dataset(db_session: Session, project: Project, experiment: Experiment, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    # 2x2 factorial: Strain (WT, MUT) x Temp (30, 37) with 3 replicates per cell (12 rows total)
    csv_data = (
        "strain,temperature,fluorescence\n"
        "WT,30,10.0\nWT,30,11.0\nWT,30,10.5\n"
        "WT,37,15.0\nWT,37,16.0\nWT,37,15.5\n"
        "MUT,30,20.0\nMUT,30,21.0\nMUT,30,20.5\n"
        "MUT,37,35.0\nMUT,37,36.0\nMUT,37,35.5\n"
    )
    file_bytes = csv_data.encode("utf-8")
    rel_path = storage.save_file(dataset_id, "strain_temp.csv", file_bytes)

    ds = Dataset(
        id=dataset_id,
        project_id=project.id,
        experiment_id=experiment.id,
        name="Strain Temp Dataset",
        file_name="strain_temp.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=12,
        column_count=3,
        storage_path=rel_path,
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)
    return ds


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageService:
    return LocalStorageService(base_dir=tmp_path / "datasets")


# 1. Successful factorial analysis execution and persistence
def test_successful_factorial_analysis_service_execution(
    db_session: Session, experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    req = FactorialComparisonCreate(
        name="Strain x Temp ANOVA",
        description="Testing interaction between strain and temperature",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
        alpha=0.05,
        post_hoc_method=PostHocMethod.TUKEY,
        check_assumptions=True,
    )

    fcomp = service.run_factorial_analysis(experiment.id, req)

    assert fcomp.id is not None
    assert fcomp.experiment_id == experiment.id
    assert fcomp.dataset_id == dataset.id
    assert fcomp.status == "completed"
    assert fcomp.name == "Strain x Temp ANOVA"
    assert fcomp.analysis_id is not None

    # Verify Analysis ORM record
    analysis = db_session.scalar(select(Analysis).where(Analysis.id == fcomp.analysis_id))
    assert analysis is not None
    assert analysis.experiment_id == experiment.id
    assert analysis.dataset_id == dataset.id
    assert analysis.analysis_type == "two_way_anova"

    # Verify statistical results in summary
    assert "effects" in fcomp.result_summary
    assert "strain" in fcomp.result_summary["effects"]
    assert "temperature" in fcomp.result_summary["effects"]
    assert f"{req.factor_a_column} \u00d7 {req.factor_b_column}" in fcomp.result_summary["effects"]
    assert "scientific_statement" in fcomp.result_summary
    assert fcomp.result_summary["is_balanced"] is True


# 2. Dataset belonging to the requested experiment
def test_dataset_not_belonging_to_experiment_raises(
    db_session: Session, other_experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    req = FactorialComparisonCreate(
        name="Mismatched Dataset Test",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )

    with pytest.raises(ScientificValidationError, match="does not belong to experiment"):
        service.run_factorial_analysis(other_experiment.id, req)


# 3. Invalid experiment and dataset identifiers
def test_invalid_experiment_and_dataset_ids(
    db_session: Session, experiment: Experiment, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    # Invalid experiment ID
    req = FactorialComparisonCreate(
        name="Invalid Exp Test",
        dataset_id=uuid.uuid4(),
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    with pytest.raises(ExperimentNotFoundError):
        service.run_factorial_analysis(uuid.uuid4(), req)

    # Invalid dataset ID
    with pytest.raises(DatasetNotFoundError):
        service.run_factorial_analysis(experiment.id, req)


# 4. Missing or invalid selected columns
def test_missing_or_invalid_selected_columns(
    db_session: Session, experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    # Nonexistent column
    req_missing = FactorialComparisonCreate(
        name="Missing Column Test",
        dataset_id=dataset.id,
        factor_a_column="nonexistent_col",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    with pytest.raises(ScientificValidationError, match="not found in dataset"):
        service.run_factorial_analysis(experiment.id, req_missing)

    # Identical factor columns
    req_same_factors = FactorialComparisonCreate(
        name="Identical Factors Test",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="strain",
        measurement_column="fluorescence",
    )
    with pytest.raises(ScientificValidationError, match="must be distinct"):
        service.run_factorial_analysis(experiment.id, req_same_factors)

    # Measurement column same as factor column
    req_meas_same = FactorialComparisonCreate(
        name="Measurement Same As Factor",
        dataset_id=dataset.id,
        factor_a_column="fluorescence",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    with pytest.raises(ScientificValidationError, match="Measurement column cannot be identical"):
        service.run_factorial_analysis(experiment.id, req_meas_same)


# 5. Invalid factor ownership (cross-experiment factor rejection)
def test_invalid_factor_ownership_cross_experiment(
    db_session: Session,
    experiment: Experiment,
    other_experiment: Experiment,
    dataset: Dataset,
    storage: LocalStorageService,
):
    service = FactorialAnalysisService(db_session, storage=storage)

    # Create factor belonging to other_experiment
    foreign_factor = ExperimentalFactor(
        experiment_id=other_experiment.id,
        name="ForeignFactor",
    )
    db_session.add(foreign_factor)
    db_session.commit()

    req = FactorialComparisonCreate(
        name="Foreign Factor Test",
        dataset_id=dataset.id,
        factor_a_id=foreign_factor.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )

    with pytest.raises(ScientificValidationError, match="does not belong to experiment"):
        service.run_factorial_analysis(experiment.id, req)

    # Identical factor IDs
    local_factor = ExperimentalFactor(experiment_id=experiment.id, name="LocalFactor")
    db_session.add(local_factor)
    db_session.commit()

    req_same_id = FactorialComparisonCreate(
        name="Same Factor ID Test",
        dataset_id=dataset.id,
        factor_a_id=local_factor.id,
        factor_b_id=local_factor.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    with pytest.raises(ScientificValidationError, match="must reference distinct factor definitions"):
        service.run_factorial_analysis(experiment.id, req_same_id)


# 6 & 7. Persistence, correct provenance, and retrieval
def test_persistence_and_provenance(
    db_session: Session, experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    # Create persisted factor definitions for full provenance
    f_strain = ExperimentalFactor(experiment_id=experiment.id, name="StrainFactor", factor_type="genetic")
    f_temp = ExperimentalFactor(experiment_id=experiment.id, name="TempFactor", factor_type="environmental")
    db_session.add_all([f_strain, f_temp])
    db_session.commit()

    req = FactorialComparisonCreate(
        name="Provenance Verified ANOVA",
        description="Verifying full provenance chain",
        dataset_id=dataset.id,
        factor_a_id=f_strain.id,
        factor_b_id=f_temp.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
        alpha=0.01,
        post_hoc_method=PostHocMethod.BONFERRONI,
    )

    created = service.run_factorial_analysis(experiment.id, req)

    # Retrieve and verify relationships
    fetched = service.get_by_id(created.id, experiment_id=experiment.id)
    assert fetched is not None
    assert fetched.factor_a.name == "StrainFactor"
    assert fetched.factor_b.name == "TempFactor"
    assert fetched.analysis.parameters["alpha"] == 0.01
    assert fetched.analysis.parameters["post_hoc_method"] == "bonferroni"
    assert fetched.dataset.name == "Strain Temp Dataset"


# 8 & 9. Scientific-engine validation errors propagate and leave NO phantom records
def test_scientific_engine_validation_error_leaves_no_phantom_record(
    db_session: Session, project: Project, experiment: Experiment, storage: LocalStorageService
):
    # Create dataset with non-numeric response column
    bad_ds_id = uuid.uuid4()
    bad_csv = b"fa,fb,resp\nA,X,not_a_number\nA,Y,invalid\nB,X,text\nB,Y,bad\n"
    rel_path = storage.save_file(bad_ds_id, "bad_data.csv", bad_csv)

    bad_ds = Dataset(
        id=bad_ds_id,
        project_id=project.id,
        experiment_id=experiment.id,
        name="Bad Numeric Dataset",
        file_name="bad_data.csv",
        file_type="csv",
        file_size=len(bad_csv),
        row_count=4,
        column_count=3,
        storage_path=rel_path,
    )
    db_session.add(bad_ds)
    db_session.commit()

    service = FactorialAnalysisService(db_session, storage=storage)

    req = FactorialComparisonCreate(
        name="Should Fail Execution",
        dataset_id=bad_ds.id,
        factor_a_column="fa",
        factor_b_column="fb",
        measurement_column="resp",
    )

    # Scientific engine should reject non-numeric column
    with pytest.raises(ScientificValidationError):
        service.run_factorial_analysis(experiment.id, req)

    # Ensure no Analysis or FactorialComparison records exist in DB
    existing_analyses = db_session.scalars(
        select(Analysis).where(Analysis.dataset_id == bad_ds_id)
    ).all()
    assert len(existing_analyses) == 0

    existing_fcomps = db_session.scalars(
        select(FactorialComparison).where(FactorialComparison.dataset_id == bad_ds_id)
    ).all()
    assert len(existing_fcomps) == 0


# 10 & 11. Listing analyses by experiment
def test_listing_factorial_comparisons_by_experiment(
    db_session: Session, experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    req1 = FactorialComparisonCreate(
        name="Analysis 1",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    req2 = FactorialComparisonCreate(
        name="Analysis 2",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )

    service.run_factorial_analysis(experiment.id, req1)
    service.run_factorial_analysis(experiment.id, req2)

    comps = service.list_by_experiment(experiment.id)
    assert len(comps) == 2
    names = [c.name for c in comps]
    assert "Analysis 1" in names
    assert "Analysis 2" in names


# 12. Update and Delete lifecycle
def test_update_and_delete_factorial_comparison(
    db_session: Session, experiment: Experiment, dataset: Dataset, storage: LocalStorageService
):
    service = FactorialAnalysisService(db_session, storage=storage)

    req = FactorialComparisonCreate(
        name="Original Name",
        description="Original Desc",
        dataset_id=dataset.id,
        factor_a_column="strain",
        factor_b_column="temperature",
        measurement_column="fluorescence",
    )
    fcomp = service.run_factorial_analysis(experiment.id, req)
    analysis_id = fcomp.analysis_id

    # Update metadata
    updated = service.update(
        fcomp.id,
        FactorialComparisonUpdate(name="Renamed ANOVA", description="Updated Desc"),
        experiment_id=experiment.id,
    )
    assert updated is not None
    assert updated.name == "Renamed ANOVA"
    assert updated.description == "Updated Desc"

    # Delete
    deleted = service.delete(fcomp.id, experiment_id=experiment.id)
    assert deleted is True

    # Check that both FactorialComparison and linked Analysis are deleted
    assert service.get_by_id(fcomp.id) is None
    assert db_session.scalar(select(Analysis).where(Analysis.id == analysis_id)) is None


# 13. FactorService CRUD
def test_factor_service_crud_and_validation(db_session: Session, experiment: Experiment):
    factor_service = FactorService(db_session)

    schema = ExperimentalFactorCreate(
        name="Inducer",
        description="Chemical inducer concentration",
        factor_type="chemical",
        levels=[
            FactorLevelCreate(name="0uM", order_index=0),
            FactorLevelCreate(name="100uM", order_index=1),
        ],
    )

    factor = factor_service.create_factor(experiment.id, schema)
    assert factor.id is not None
    assert factor.name == "Inducer"
    assert len(factor.levels) == 2

    # Duplicate name should raise error
    with pytest.raises(ScientificValidationError, match="already exists"):
        factor_service.create_factor(experiment.id, schema)

    # List factors
    factors = factor_service.list_factors(experiment.id)
    assert len(factors) >= 1

    # Delete factor
    success = factor_service.delete_factor(experiment.id, factor.id)
    assert success is True
    assert factor_service.get_factor(factor.id) is None
