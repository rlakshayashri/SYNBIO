import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ScientificValidationError
from app.models.dataset import Dataset
from app.models.project import Project
from app.schemas.comparison import ComparisonCreateRequest
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate
from app.schemas.experimental_group import ExperimentalGroupCreate
from app.schemas.replicate import ReplicateCreate
from app.services.comparison_service import ComparisonService
from app.services.experiment_service import ExperimentService
from app.services.group_service import GroupService
from app.services.replicate_service import ReplicateService
from app.storage.local import LocalStorageService


@pytest.fixture
def test_project(db_session: Session) -> Project:
    project = Project(name="Test Project", description="Test Description")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_dataset(db_session: Session, test_project: Project, tmp_path: Path) -> Dataset:
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    dataset_id = uuid.uuid4()
    file_bytes = b"group,yield\nCTRL,10.5\nCTRL,11.2\nCTRL,10.8\nTRT,20.1\nTRT,21.3\nTRT,20.8\n"
    rel_path = storage.save_file(dataset_id, "test_exp_data.csv", file_bytes)

    dataset = Dataset(
        id=dataset_id,
        project_id=test_project.id,
        name="Test Exp Dataset",
        file_name="test_exp_data.csv",
        file_type="csv",
        file_size=len(file_bytes),
        row_count=6,
        column_count=2,
        storage_path=rel_path,
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset


def test_experiment_service_crud(db_session: Session, test_project: Project):
    service = ExperimentService(db_session)
    schema = ExperimentCreate(
        project_id=test_project.id,
        name="GFP Expression Study",
        organism="E. coli",
        condition_type="Temperature",
        groups=[
            ExperimentalGroupCreate(
                name="Control 37C",
                group_code="CTRL",
                is_control=True,
                replicates=[ReplicateCreate(replicate_name="Rep_1")],
            ),
        ],
    )

    exp = service.create(schema)
    assert exp.id is not None
    assert exp.name == "GFP Expression Study"

    updated = service.update(exp.id, ExperimentUpdate(name="Updated Study"))
    assert updated is not None
    assert updated.name == "Updated Study"

    all_exps = service.list_all(project_id=test_project.id)
    assert len(all_exps) == 1

    success = service.delete(exp.id)
    assert success is True


def test_group_and_replicate_services(db_session: Session, test_project: Project):
    exp_service = ExperimentService(db_session)
    group_service = GroupService(db_session)
    replicate_service = ReplicateService(db_session)

    exp = exp_service.create(ExperimentCreate(project_id=test_project.id, name="Group Test Exp"))

    # Add Group
    group = group_service.create(exp.id, ExperimentalGroupCreate(name="Test Group", group_code="TG"))
    assert group.id is not None
    assert group.experiment_id == exp.id

    # Add Replicate
    rep = replicate_service.create(group.id, ReplicateCreate(replicate_name="Rep_10"))
    assert rep.id is not None
    assert rep.group_id == group.id


def test_comparison_service_valid_flow(
    db_session: Session, test_project: Project, test_dataset: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    group_service = GroupService(db_session)
    comp_service = ComparisonService(db_session, storage=storage)

    exp_create = ExperimentCreate(project_id=test_project.id, dataset_id=test_dataset.id, name="Comparison Exp")
    exp = exp_service.create(exp_create)
    g1 = group_service.create(exp.id, ExperimentalGroupCreate(name="Control", group_code="CTRL", is_control=True))
    g2 = group_service.create(exp.id, ExperimentalGroupCreate(name="Treatment", group_code="TRT", is_control=False))

    comp_req = ComparisonCreateRequest(
        name="CTRL vs TRT Comparison",
        comparison_type="two_group",
        group_a_id=g1.id,
        group_b_id=g2.id,
        measurement_column="yield",
        group_column="group",
    )

    comparison = comp_service.run_comparison(exp.id, comp_req)
    assert comparison.id is not None
    assert comparison.experiment_id == exp.id
    assert comparison.analysis_id is not None
    assert "statistical_result" in comparison.result_summary


def test_comparison_service_same_group_validation(
    db_session: Session, test_project: Project, test_dataset: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    group_service = GroupService(db_session)
    comp_service = ComparisonService(db_session, storage=storage)

    exp_create = ExperimentCreate(project_id=test_project.id, dataset_id=test_dataset.id, name="Same Group Exp")
    exp = exp_service.create(exp_create)
    g1 = group_service.create(exp.id, ExperimentalGroupCreate(name="Control", group_code="CTRL"))

    comp_req = ComparisonCreateRequest(
        name="Invalid Comparison",
        comparison_type="two_group",
        group_a_id=g1.id,
        group_b_id=g1.id,
        measurement_column="yield",
        group_column="group",
    )

    with pytest.raises(ScientificValidationError, match="distinct"):
        comp_service.run_comparison(exp.id, comp_req)


def test_comparison_service_cross_experiment_group_validation(
    db_session: Session, test_project: Project, test_dataset: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    group_service = GroupService(db_session)
    comp_service = ComparisonService(db_session, storage=storage)

    exp1 = exp_service.create(
        ExperimentCreate(project_id=test_project.id, dataset_id=test_dataset.id, name="Exp 1")
    )
    exp2 = exp_service.create(
        ExperimentCreate(project_id=test_project.id, dataset_id=test_dataset.id, name="Exp 2")
    )

    g1 = group_service.create(exp1.id, ExperimentalGroupCreate(name="Control Exp1", group_code="CTRL"))
    g2_cross = group_service.create(exp2.id, ExperimentalGroupCreate(name="Treatment Exp2", group_code="TRT"))

    comp_req = ComparisonCreateRequest(
        name="Cross Exp Comparison",
        comparison_type="two_group",
        group_a_id=g1.id,
        group_b_id=g2_cross.id,
        measurement_column="yield",
        group_column="group",
    )

    with pytest.raises(ScientificValidationError, match="does not belong to experiment"):
        comp_service.run_comparison(exp1.id, comp_req)


def test_comparison_service_missing_group_validation(
    db_session: Session, test_project: Project, test_dataset: Dataset, tmp_path: Path
):
    storage = LocalStorageService(base_dir=tmp_path / "datasets")
    exp_service = ExperimentService(db_session)
    group_service = GroupService(db_session)
    comp_service = ComparisonService(db_session, storage=storage)

    exp_create = ExperimentCreate(project_id=test_project.id, dataset_id=test_dataset.id, name="Missing Group Exp")
    exp = exp_service.create(exp_create)
    g1 = group_service.create(exp.id, ExperimentalGroupCreate(name="Control", group_code="CTRL"))

    comp_req = ComparisonCreateRequest(
        name="Missing Group Comparison",
        comparison_type="two_group",
        group_a_id=g1.id,
        group_b_id=uuid.uuid4(),
        measurement_column="yield",
        group_column="group",
    )

    with pytest.raises(ScientificValidationError, match="not found"):
        comp_service.run_comparison(exp.id, comp_req)
