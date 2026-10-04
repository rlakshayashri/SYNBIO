import csv
import io
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.schemas.results import (
    ComparisonProvenanceSummary,
    DatasetProvenanceSummary,
    ExperimentProvenanceSummary,
    ExperimentResultItem,
    ExperimentResultsResponse,
    ResultProvenance,
)


class ExperimentResultsService:
    """Service encapsulating results aggregation, provenance assembly, and scientific export."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_results(
        self,
        experiment_id: UUID,
        analysis_type: str | None = None,
        dataset_id: UUID | None = None,
    ) -> ExperimentResultsResponse:
        """Retrieves and normalizes all Analysis records for an experiment with full provenance."""
        experiment = self.db.scalar(select(Experiment).where(Experiment.id == experiment_id))
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        # Find attached dataset IDs
        attached_dataset_ids = list(
            self.db.scalars(
                select(Dataset.id).where(Dataset.experiment_id == experiment_id)
            ).all()
        )

        # Build query for Analyses linked to this experiment OR attached datasets
        stmt = (
            select(Analysis)
            .options(
                joinedload(Analysis.dataset),
                joinedload(Analysis.experiment),
                joinedload(Analysis.comparison).joinedload(Comparison.group_a),
                joinedload(Analysis.comparison).joinedload(Comparison.group_b),
            )
            .where(
                or_(
                    Analysis.experiment_id == experiment_id,
                    Analysis.dataset_id.in_(attached_dataset_ids) if attached_dataset_ids else False,
                )
            )
        )

        if analysis_type:
            stmt = stmt.where(Analysis.analysis_type == analysis_type)
        if dataset_id:
            stmt = stmt.where(Analysis.dataset_id == dataset_id)

        stmt = stmt.order_by(Analysis.created_at.desc())
        analyses = list(self.db.scalars(stmt).unique().all())

        result_items: list[ExperimentResultItem] = []
        for a in analyses:
            # Build Dataset Summary
            dataset_summary = DatasetProvenanceSummary(
                id=a.dataset.id,
                name=a.dataset.name or a.dataset.file_name,
                file_name=a.dataset.file_name,
            )

            # Build Experiment Summary
            exp_summary = ExperimentProvenanceSummary(
                id=experiment.id,
                name=experiment.name,
            )

            # Build Comparison Summary if linked
            comp_summary: ComparisonProvenanceSummary | None = None
            if a.comparison:
                comp = a.comparison
                comp_summary = ComparisonProvenanceSummary(
                    id=comp.id,
                    name=comp.name,
                    comparison_type=comp.comparison_type,
                    group_a_name=comp.group_a.name if comp.group_a else None,
                    group_b_name=comp.group_b.name if comp.group_b else None,
                    group_column=comp.group_column,
                    measurement_column=comp.measurement_column,
                    method=comp.parameters.get("method") if comp.parameters else None,
                )

            provenance = ResultProvenance(
                experiment_id=experiment.id,
                dataset_id=a.dataset_id,
                analysis_id=a.id,
                comparison_id=a.comparison.id if a.comparison else None,
                software_version=a.software_version,
            )

            result_items.append(
                ExperimentResultItem(
                    analysis_id=a.id,
                    analysis_type=a.analysis_type,
                    created_at=a.created_at,
                    software_version=a.software_version,
                    dataset=dataset_summary,
                    experiment=exp_summary,
                    comparison=comp_summary,
                    provenance=provenance,
                    parameters=a.parameters or {},
                    result=a.result or {},
                )
            )

        return ExperimentResultsResponse(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            total_results=len(result_items),
            results=result_items,
        )

    def export_csv(self, experiment_id: UUID) -> str:
        """Generates structured CSV export representing tabular provenance index and key scalar metrics."""
        response = self.get_results(experiment_id)

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "analysis_id",
            "analysis_type",
            "created_at",
            "software_version",
            "experiment_id",
            "experiment_name",
            "dataset_id",
            "dataset_name",
            "comparison_id",
            "comparison_name",
            "statistical_method",
            "group_a",
            "group_b",
            "group_column",
            "measurement_column",
            "statistic_name",
            "statistic_value",
            "p_value",
            "is_significant",
        ]
        writer.writerow(headers)

        for item in response.results:
            stat_res = item.result.get("statistical_result") or {}
            comp = item.comparison

            writer.writerow([
                str(item.analysis_id),
                item.analysis_type,
                item.created_at.isoformat(),
                item.software_version,
                str(item.experiment.id),
                item.experiment.name,
                str(item.dataset.id),
                item.dataset.name,
                str(comp.id) if comp else "",
                comp.name if comp else "",
                comp.method if comp else (stat_res.get("method") or ""),
                comp.group_a_name if comp else "",
                comp.group_b_name if comp else "",
                comp.group_column if comp else "",
                comp.measurement_column if comp else "",
                stat_res.get("statistic_name") or "",
                stat_res.get("statistic_value") if stat_res.get("statistic_value") is not None else "",
                stat_res.get("p_value") if stat_res.get("p_value") is not None else "",
                stat_res.get("is_significant") if stat_res.get("is_significant") is not None else "",
            ])

        return output.getvalue()
