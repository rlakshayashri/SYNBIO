from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.schemas.analysis import AnalysisResponse
from app.schemas.comparison import ComparisonResponse
from app.schemas.dataset import DatasetResponse
from app.schemas.experiment import (
    ExperimentResponse,
    ExperimentWorkspaceResponse,
)
from app.schemas.experimental_group import ExperimentalGroupResponse


class ExperimentWorkspaceService:
    """Read-only service for composing lightweight Experiment Workspace metadata summaries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_workspace(self, experiment_id: UUID) -> ExperimentWorkspaceResponse:
        """Retrieves and composes lightweight metadata summaries for the experiment workspace view.

        Strictly read-only composition of existing metadata records. Executes no scientific computations.
        """
        stmt = (
            select(Experiment)
            .options(
                joinedload(Experiment.groups).joinedload(ExperimentalGroup.replicates),
                joinedload(Experiment.comparisons),
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = self.db.scalar(stmt)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        # 1. Fetch attached datasets
        ds_stmt = (
            select(Dataset)
            .where(Dataset.experiment_id == experiment_id)
            .order_by(Dataset.created_at.desc())
        )
        attached_datasets = list(self.db.scalars(ds_stmt).all())

        # Include primary dataset if experiment.dataset_id is set and not already in attached_datasets list
        if experiment.dataset_id:
            primary_ds = self.db.scalar(select(Dataset).where(Dataset.id == experiment.dataset_id))
            if primary_ds and not any(d.id == primary_ds.id for d in attached_datasets):
                attached_datasets.insert(0, primary_ds)

        # 2. Fetch associated analyses (linked directly to experiment or to attached datasets)
        dataset_ids = [d.id for d in attached_datasets]
        an_stmt = select(Analysis).order_by(Analysis.created_at.desc())
        if dataset_ids:
            an_stmt = an_stmt.where(
                (Analysis.experiment_id == experiment_id) | (Analysis.dataset_id.in_(dataset_ids))
            )
        else:
            an_stmt = an_stmt.where(Analysis.experiment_id == experiment_id)

        analyses = list(self.db.scalars(an_stmt).unique().all())

        # 3. Build Pydantic response DTOs
        exp_dto = ExperimentResponse.model_validate(experiment)
        datasets_dtos = [DatasetResponse.model_validate(d) for d in attached_datasets]
        groups_dtos = [ExperimentalGroupResponse.model_validate(g) for g in experiment.groups]
        comparisons_dtos = [ComparisonResponse.model_validate(c) for c in experiment.comparisons]
        analyses_dtos = [AnalysisResponse.model_validate(a) for a in analyses]

        return ExperimentWorkspaceResponse(
            experiment=exp_dto,
            attached_datasets=datasets_dtos,
            groups=groups_dtos,
            comparisons=comparisons_dtos,
            analyses=analyses_dtos,
        )
