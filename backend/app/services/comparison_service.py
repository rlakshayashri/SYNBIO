from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DatasetNotFoundError,
    ExperimentNotFoundError,
    ScientificValidationError,
)
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.schemas.comparison import ComparisonCreateRequest
from app.scientific.comparison import execute_experimental_comparison
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.services.dataset_service import DatasetService
from app.storage.local import LocalStorageService


class ComparisonService:
    """Service encapsulating validation, scientific orchestration, and persistence for Comparisons."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def get_by_id(self, comparison_id: UUID) -> Comparison | None:
        """Retrieves a single Comparison record by ID."""
        return self.db.scalar(select(Comparison).where(Comparison.id == comparison_id))

    def run_comparison(self, experiment_id: UUID, request: ComparisonCreateRequest) -> Comparison:
        """Validates comparison parameters, orchestrates scientific comparison, and persists records."""
        # Check 4 — Validate experiment & linked dataset
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        if not experiment.dataset_id:
            raise ScientificValidationError(
                f"Experiment '{experiment.name}' is not linked to a dataset. Link a dataset to execute comparisons."
            )

        dataset_service = DatasetService(self.db)
        dataset = dataset_service.get_by_id(experiment.dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Linked dataset with ID '{experiment.dataset_id}' not found.")

        # Check 1 — Same group validation
        if request.group_a_id and request.group_b_id and request.group_a_id == request.group_b_id:
            raise ScientificValidationError(
                "Group A and Group B must be distinct experimental groups. A group cannot be compared against itself."
            )

        # Check 2 — Validate Group A exists and belongs to this experiment
        group_a_code: str | None = None
        if request.group_a_id:
            g_a = self.db.scalar(select(ExperimentalGroup).where(ExperimentalGroup.id == request.group_a_id))
            if not g_a:
                raise ScientificValidationError(f"Group A with ID '{request.group_a_id}' not found.")
            if g_a.experiment_id != experiment_id:
                raise ScientificValidationError(
                    f"Group A '{g_a.name}' does not belong to experiment '{experiment_id}'."
                )
            group_a_code = g_a.group_code

        # Check 3 — Validate Group B exists and belongs to this experiment
        group_b_code: str | None = None
        if request.group_b_id:
            g_b = self.db.scalar(select(ExperimentalGroup).where(ExperimentalGroup.id == request.group_b_id))
            if not g_b:
                raise ScientificValidationError(f"Group B with ID '{request.group_b_id}' not found.")
            if g_b.experiment_id != experiment_id:
                raise ScientificValidationError(
                    f"Group B '{g_b.name}' does not belong to experiment '{experiment_id}'."
                )
            group_b_code = g_b.group_code

        # Load dataset and execute scientific engine
        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        comp_dict = execute_experimental_comparison(
            df=df,
            measurement_column=request.measurement_column,
            comparison_type=request.comparison_type,
            group_column=request.group_column,
            group_a_code=group_a_code,
            group_b_code=group_b_code,
            method=request.method,
            alpha=request.alpha,
            paired=request.paired,
            post_hoc_method=request.post_hoc_method,
        )

        group_summaries = [gs.model_dump(mode="json") for gs in comp_dict["group_summaries"]]
        stat_res = comp_dict["statistical_result"]

        # Persist Analysis ORM record
        analysis_record = Analysis(
            dataset_id=dataset.id,
            experiment_id=experiment_id,
            analysis_type=f"experimental_comparison_{request.comparison_type}_{request.method.value}",
            parameters=request.model_dump(mode="json"),
            result={
                "statistical_result": stat_res.model_dump(mode="json"),
                "group_summaries": group_summaries,
            },
        )
        self.db.add(analysis_record)
        self.db.flush()

        # Persist Comparison ORM record
        comparison_record = Comparison(
            experiment_id=experiment_id,
            analysis_id=analysis_record.id,
            name=request.name,
            comparison_type=request.comparison_type,
            group_a_id=request.group_a_id,
            group_b_id=request.group_b_id,
            measurement_column=request.measurement_column,
            group_column=request.group_column,
            parameters=request.model_dump(mode="json"),
            result_summary={
                "statistical_result": stat_res.model_dump(mode="json"),
                "group_summaries": group_summaries,
            },
        )
        self.db.add(comparison_record)
        self.db.commit()
        self.db.refresh(comparison_record)
        return comparison_record
