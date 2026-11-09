from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    DatasetNotFoundError,
    ExperimentNotFoundError,
    ScientificValidationError,
)
from app.models.analysis import Analysis
from app.models.experiment import Experiment
from app.models.experimental_factor import ExperimentalFactor
from app.models.factorial_comparison import FactorialComparison
from app.schemas.factorial_comparison import (
    FactorialComparisonCreate,
    FactorialComparisonUpdate,
)
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.scientific.statistics.factorial_models import FactorialAnalysisOptions
from app.scientific.statistics.models import PostHocMethod
from app.scientific.statistics.two_way_anova import compute_two_way_anova
from app.services.dataset_service import DatasetService
from app.storage.local import LocalStorageService


class FactorialAnalysisService:
    """Service orchestrating Two-Way ANOVA factorial analysis, dataset loading, and persistence."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def get_by_id(
        self, comparison_id: UUID, experiment_id: UUID | None = None
    ) -> FactorialComparison | None:
        """Retrieves a single FactorialComparison by ID, optionally verifying experiment ownership."""
        stmt = (
            select(FactorialComparison)
            .options(
                joinedload(FactorialComparison.factor_a),
                joinedload(FactorialComparison.factor_b),
                joinedload(FactorialComparison.analysis),
                joinedload(FactorialComparison.dataset),
            )
            .where(FactorialComparison.id == comparison_id)
        )
        if experiment_id:
            stmt = stmt.where(FactorialComparison.experiment_id == experiment_id)
        return self.db.scalar(stmt)

    def list_by_experiment(self, experiment_id: UUID) -> Sequence[FactorialComparison]:
        """Lists all FactorialComparisons associated with an experiment."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        stmt = (
            select(FactorialComparison)
            .options(
                joinedload(FactorialComparison.factor_a),
                joinedload(FactorialComparison.factor_b),
                joinedload(FactorialComparison.analysis),
                joinedload(FactorialComparison.dataset),
            )
            .where(FactorialComparison.experiment_id == experiment_id)
            .order_by(FactorialComparison.created_at.desc())
        )
        return self.db.scalars(stmt).unique().all()

    def run_factorial_analysis(
        self, experiment_id: UUID, request: FactorialComparisonCreate
    ) -> FactorialComparison:
        """Validates experiment, dataset, factors, and data, runs pure scientific Two-Way ANOVA,

        and persists Analysis and FactorialComparison records atomically.
        """
        # 1. Validate Target Experiment
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        # 2. Resolve and Validate Target Dataset
        target_dataset_id = request.dataset_id or experiment.dataset_id
        if not target_dataset_id:
            raise ScientificValidationError(
                f"Experiment '{experiment.name}' is not linked to a dataset. "
                "Link a dataset to the experiment or provide a dataset_id."
            )

        dataset_service = DatasetService(self.db, storage=self.storage)
        dataset = dataset_service.get_by_id(target_dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{target_dataset_id}' not found.")

        # Verify dataset belongs to experiment
        if dataset.experiment_id != experiment_id and experiment.dataset_id != dataset.id:
            raise ScientificValidationError(
                f"Dataset '{dataset.id}' does not belong to experiment '{experiment_id}'."
            )

        # 3. Validate Persisted Factor Definitions (if provided)
        if request.factor_a_id and request.factor_b_id and request.factor_a_id == request.factor_b_id:
            raise ScientificValidationError("Factor A and Factor B must reference distinct factor definitions.")

        factor_a: ExperimentalFactor | None = None
        if request.factor_a_id:
            factor_a = self.db.scalar(
                select(ExperimentalFactor)
                .options(joinedload(ExperimentalFactor.levels))
                .where(ExperimentalFactor.id == request.factor_a_id)
            )
            if not factor_a:
                raise ScientificValidationError(f"Factor A with ID '{request.factor_a_id}' not found.")
            if factor_a.experiment_id != experiment_id:
                raise ScientificValidationError(
                    f"Factor A '{factor_a.name}' does not belong to experiment '{experiment_id}'."
                )

        factor_b: ExperimentalFactor | None = None
        if request.factor_b_id:
            factor_b = self.db.scalar(
                select(ExperimentalFactor)
                .options(joinedload(ExperimentalFactor.levels))
                .where(ExperimentalFactor.id == request.factor_b_id)
            )
            if not factor_b:
                raise ScientificValidationError(f"Factor B with ID '{request.factor_b_id}' not found.")
            if factor_b.experiment_id != experiment_id:
                raise ScientificValidationError(
                    f"Factor B '{factor_b.name}' does not belong to experiment '{experiment_id}'."
                )

        # 4. Validate Dataset Column Names and Load Observation Data
        if request.factor_a_column == request.factor_b_column:
            raise ScientificValidationError(
                f"Factor A column and Factor B column must be distinct ('{request.factor_a_column}')."
            )
        if (
            request.factor_a_column == request.measurement_column
            or request.factor_b_column == request.measurement_column
        ):
            raise ScientificValidationError(
                "Measurement column cannot be identical to Factor A or Factor B column."
            )

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        missing_cols = [
            c
            for c in [request.factor_a_column, request.factor_b_column, request.measurement_column]
            if c not in df.columns
        ]
        if missing_cols:
            raise ScientificValidationError(
                f"Requested column(s) {missing_cols} not found in dataset '{dataset.name}'. "
                f"Available columns: {list(df.columns)}"
            )

        # 5. Execute Pure Scientific Two-Way ANOVA Engine
        alpha = (
            request.parameters.get("alpha")
            if (request.parameters and "alpha" in request.parameters)
            else request.alpha
        )
        post_hoc_raw = (
            request.parameters.get("post_hoc_method")
            if (request.parameters and "post_hoc_method" in request.parameters)
            else request.post_hoc_method
        )
        post_hoc_method = (
            PostHocMethod(post_hoc_raw) if isinstance(post_hoc_raw, str) else post_hoc_raw
        )
        check_assumptions = (
            request.parameters.get("check_assumptions")
            if (request.parameters and "check_assumptions" in request.parameters)
            else request.check_assumptions
        )

        options = FactorialAnalysisOptions(
            alpha=alpha,
            type_ss=3,
            post_hoc_method=post_hoc_method,
            check_assumptions=check_assumptions,
        )

        # 5. Execute Pure Scientific Two-Way ANOVA Engine
        anova_result = compute_two_way_anova(
            df=df,
            response_column=request.measurement_column,
            factor_a_column=request.factor_a_column,
            factor_b_column=request.factor_b_column,
            options=options,
        )

        # 6. Persist Analysis and FactorialComparison Records Atomically
        result_dict = anova_result.model_dump(mode="json")
        exec_params = {
            "factor_a_column": request.factor_a_column,
            "factor_b_column": request.factor_b_column,
            "measurement_column": request.measurement_column,
            "alpha": alpha,
            "type_ss": 3,
            "post_hoc_method": post_hoc_method.value,
            "check_assumptions": check_assumptions,
            "contrast_coding": "sum-to-zero (deviation)",
            **request.parameters,
        }

        try:
            analysis_record = Analysis(
                dataset_id=dataset.id,
                experiment_id=experiment_id,
                analysis_type="two_way_anova",
                parameters=exec_params,
                result=result_dict,
            )
            self.db.add(analysis_record)
            self.db.flush()

            fcomp = FactorialComparison(
                experiment_id=experiment_id,
                analysis_id=analysis_record.id,
                dataset_id=dataset.id,
                name=request.name,
                status="completed",
                description=request.description,
                factor_a_id=request.factor_a_id,
                factor_b_id=request.factor_b_id,
                factor_a_column=request.factor_a_column,
                factor_b_column=request.factor_b_column,
                measurement_column=request.measurement_column,
                parameters=exec_params,
                result_summary=result_dict,
            )
            self.db.add(fcomp)
            self.db.commit()
            self.db.refresh(fcomp)
            return fcomp
        except Exception:
            self.db.rollback()
            raise

    def update(
        self,
        comparison_id: UUID,
        schema: FactorialComparisonUpdate,
        experiment_id: UUID | None = None,
    ) -> FactorialComparison | None:
        """Updates metadata (name, description) on an existing FactorialComparison."""
        fcomp = self.get_by_id(comparison_id, experiment_id=experiment_id)
        if not fcomp:
            return None

        if schema.name is not None:
            fcomp.name = schema.name
        if schema.description is not None:
            fcomp.description = schema.description

        self.db.commit()
        self.db.refresh(fcomp)
        return fcomp

    def delete(self, comparison_id: UUID, experiment_id: UUID | None = None) -> bool:
        """Deletes a FactorialComparison and its linked Analysis record atomically."""
        fcomp = self.get_by_id(comparison_id, experiment_id=experiment_id)
        if not fcomp:
            return False

        if fcomp.analysis_id:
            analysis = self.db.scalar(select(Analysis).where(Analysis.id == fcomp.analysis_id))
            if analysis:
                self.db.delete(analysis)

        self.db.delete(fcomp)
        self.db.commit()
        return True
