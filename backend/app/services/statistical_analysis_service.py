from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError, ScientificValidationError
from app.models.analysis import Analysis
from app.schemas.statistical_analysis import StatisticalAnalysisRequestSchema
from app.scientific.preprocessing.data_loader import load_dataset_to_dataframe
from app.scientific.statistics import (
    AnalysisCategory,
    StatisticalAnalysisResult,
    run_anova_analysis,
    run_correlation_analysis,
    run_nonparametric_group_comparison,
    run_two_group_comparison,
)
from app.services.dataset_service import DatasetService
from app.storage.local import LocalStorageService


class StatisticalAnalysisService:
    """Orchestrates statistical hypothesis testing, data loading, and analysis record persistence."""

    def __init__(self, db: Session, storage: LocalStorageService | None = None) -> None:
        self.db = db
        self.storage = storage or LocalStorageService()

    def run_statistical_analysis(
        self, dataset_id: UUID, request: StatisticalAnalysisRequestSchema
    ) -> StatisticalAnalysisResult:
        """Loads dataset file, executes scientific hypothesis test, and stores analysis record."""
        dataset_service = DatasetService(self.db)
        dataset = dataset_service.get_by_id(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset with ID '{dataset_id}' not found.")

        abs_path = self.storage.get_file_path(dataset.storage_path)
        df = load_dataset_to_dataframe(abs_path, dataset.file_type)

        if request.category == AnalysisCategory.CORRELATION:
            if not request.value_column_2:
                raise ScientificValidationError("Correlation analysis requires 'value_column_2'.")
            result = run_correlation_analysis(
                df,
                column_1=request.value_column,
                column_2=request.value_column_2,
                method=request.method,
                alpha=request.alpha,
            )
        elif request.category == AnalysisCategory.TWO_GROUP:
            result = run_two_group_comparison(
                df,
                value_column=request.value_column,
                group_column=request.group_column,
                value_column_2=request.value_column_2,
                method=request.method,
                alpha=request.alpha,
                paired=request.paired,
            )
        elif request.category == AnalysisCategory.ANOVA:
            if not request.group_column:
                raise ScientificValidationError("ANOVA requires a 'group_column'.")
            result = run_anova_analysis(
                df,
                value_column=request.value_column,
                group_column=request.group_column,
                method=request.method,
                alpha=request.alpha,
                post_hoc_method=request.post_hoc_method,
            )
        elif request.category == AnalysisCategory.NONPARAMETRIC:
            result = run_nonparametric_group_comparison(
                df,
                value_column=request.value_column,
                group_column=request.group_column,
                value_column_2=request.value_column_2,
                method=request.method,
                alpha=request.alpha,
                post_hoc_method=request.post_hoc_method,
                paired=request.paired,
            )
        else:
            raise ScientificValidationError(f"Unsupported analysis category '{request.category}'.")

        result.dataset_id = dataset_id

        # Persist Analysis ORM record
        analysis_record = Analysis(
            dataset_id=dataset_id,
            experiment_id=dataset.experiment_id,
            analysis_type=f"statistical_analysis_{request.method.value}",
            parameters=request.model_dump(mode="json"),
            result=result.model_dump(mode="json"),
        )
        self.db.add(analysis_record)
        self.db.commit()

        return result
