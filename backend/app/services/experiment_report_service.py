from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.schemas.report import (
    ComparisonReportItem,
    DataQualityReportItem,
    DatasetReportItem,
    DescriptiveStatisticsReportItem,
    ExperimentalContextReport,
    ExperimentalGroupReportItem,
    ExperimentReport,
    ExperimentReportHeader,
    GroupReplicateReportItem,
    ProvenanceReportItem,
    StatisticalResultReportItem,
    VisualizationReportItem,
)


class ExperimentReportService:
    """Service encapsulating report aggregation, evidence assembly, and markdown rendering.

    Strictly assembles pre-existing, stored scientific evidence without running new statistical
    computations or drawing automated biological conclusions.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_report(self, experiment_id: UUID) -> ExperimentReport:
        """Assembles a structured, reproducible scientific report for an experiment."""
        stmt = (
            select(Experiment)
            .options(
                joinedload(Experiment.groups).joinedload(ExperimentalGroup.replicates),
                joinedload(Experiment.comparisons).joinedload(Comparison.group_a),
                joinedload(Experiment.comparisons).joinedload(Comparison.group_b),
            )
            .where(Experiment.id == experiment_id)
        )
        experiment = self.db.scalar(stmt)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment with ID '{experiment_id}' not found.")

        now_utc = datetime.now(UTC)

        # 1. Header Metadata
        header = ExperimentReportHeader(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            description=experiment.description,
            objective=experiment.objective,
            status=experiment.status,
            organism=experiment.organism,
            condition_type=experiment.condition_type,
            assay_type=getattr(experiment, "assay_type", None),
            target_gene=getattr(experiment, "target_gene", None),
            notes=experiment.notes,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at,
            report_generated_at=now_utc,
            software_version="0.1.0",
        )

        # 2. Experimental Context (Groups & Replicates)
        group_items: list[ExperimentalGroupReportItem] = []
        for g in experiment.groups:
            replicate_items: list[GroupReplicateReportItem] = [
                GroupReplicateReportItem(
                    id=r.id,
                    replicate_name=r.replicate_name,
                    sample_identifier=r.sample_identifier,
                    row_index=r.row_index,
                    replicate_type=r.replicate_type,
                    metadata_payload=r.metadata_payload or {},
                )
                for r in g.replicates
            ]
            group_items.append(
                ExperimentalGroupReportItem(
                    id=g.id,
                    name=g.name,
                    group_code=g.group_code,
                    is_control=g.is_control,
                    description=g.description,
                    metadata_payload=g.metadata_payload or {},
                    replicates=replicate_items,
                )
            )

        exp_context = ExperimentalContextReport(
            experiment_name=experiment.name,
            description=experiment.description,
            objective=experiment.objective,
            status=experiment.status,
            organism=experiment.organism,
            condition_type=experiment.condition_type,
            assay_type=getattr(experiment, "assay_type", None),
            target_gene=getattr(experiment, "target_gene", None),
            notes=experiment.notes,
            groups=group_items,
        )

        # 3. Attached Datasets
        ds_stmt = (
            select(Dataset)
            .where(Dataset.experiment_id == experiment_id)
            .order_by(Dataset.created_at.desc())
        )
        attached_datasets = list(self.db.scalars(ds_stmt).all())
        if experiment.dataset_id:
            primary_ds = self.db.scalar(select(Dataset).where(Dataset.id == experiment.dataset_id))
            if primary_ds and not any(d.id == primary_ds.id for d in attached_datasets):
                attached_datasets.insert(0, primary_ds)

        attached_dataset_ids = [d.id for d in attached_datasets]

        # 4. Fetch associated Analyses
        an_stmt = (
            select(Analysis)
            .options(
                joinedload(Analysis.dataset),
                joinedload(Analysis.comparison),
            )
            .order_by(Analysis.created_at.desc())
        )
        if attached_dataset_ids:
            an_stmt = an_stmt.where(
                (Analysis.experiment_id == experiment_id) | (Analysis.dataset_id.in_(attached_dataset_ids))
            )
        else:
            an_stmt = an_stmt.where(Analysis.experiment_id == experiment_id)

        analyses = list(self.db.scalars(an_stmt).unique().all())

        # Build Datasets section items
        dataset_items: list[DatasetReportItem] = []
        for d in attached_datasets:
            has_val = any(a.dataset_id == d.id and a.analysis_type == "validation" for a in analyses)
            dataset_items.append(
                DatasetReportItem(
                    dataset_id=d.id,
                    dataset_name=d.name or d.file_name,
                    file_name=d.file_name,
                    file_type=d.file_type,
                    file_size=d.file_size,
                    row_count=d.row_count,
                    column_count=d.column_count,
                    created_at=d.created_at,
                    has_validation=has_val,
                )
            )

        # 5. Data Quality / Validation Section
        data_quality_items: list[DataQualityReportItem] = []
        # 6. Descriptive Statistics Section
        desc_stats_items: list[DescriptiveStatisticsReportItem] = []
        # 7. Visualizations Section
        vis_items: list[VisualizationReportItem] = []
        # 8. Statistical Results Section
        stat_result_items: list[StatisticalResultReportItem] = []
        # 9. Provenance Section
        provenance_items: list[ProvenanceReportItem] = []

        for a in analyses:
            ds_name = a.dataset.name if a.dataset else "Attached Dataset"

            if a.analysis_type == "validation":
                res = a.result or {}
                summary = res.get("summary") or {}
                val_passed = summary.get("is_valid") if isinstance(summary, dict) else None

                data_quality_items.append(
                    DataQualityReportItem(
                        analysis_id=a.id,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        created_at=a.created_at,
                        missing_values=res.get("missing_values"),
                        duplicate_rows=(res.get("duplicate_rows") or {}).get("duplicate_count")
                        if isinstance(res.get("duplicate_rows"), dict)
                        else None,
                        detected_data_types=(res.get("data_types") or {}).get("column_types")
                        if isinstance(res.get("data_types"), dict)
                        else res.get("data_types"),
                        empty_columns=(res.get("empty_columns") or {}).get("empty_columns")
                        if isinstance(res.get("empty_columns"), dict)
                        else res.get("empty_columns"),
                        outliers_summary=(res.get("outliers") or {}).get("outlier_counts")
                        if isinstance(res.get("outliers"), dict)
                        else res.get("outliers"),
                        validation_passed=val_passed,
                    )
                )
                provenance_items.append(
                    ProvenanceReportItem(
                        section="data_quality",
                        analysis_id=a.id,
                        analysis_type=a.analysis_type,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        experiment_id=experiment.id,
                        software_version=a.software_version,
                        created_at=a.created_at,
                    )
                )

            elif a.analysis_type in ("descriptive_statistics", "statistics"):
                res = a.result or {}
                stats_dict = res.get("statistics") or res.get("column_statistics") or {}
                if isinstance(stats_dict, dict):
                    for col_name, stats in stats_dict.items():
                        if isinstance(stats, dict):
                            desc_stats_items.append(
                                DescriptiveStatisticsReportItem(
                                    analysis_id=a.id,
                                    dataset_id=a.dataset_id,
                                    dataset_name=ds_name,
                                    created_at=a.created_at,
                                    column_name=col_name,
                                    count=stats.get("count"),
                                    missing_count=stats.get("missing_count"),
                                    mean=stats.get("mean"),
                                    median=stats.get("median"),
                                    std_dev=stats.get("std_dev") or stats.get("std"),
                                    variance=stats.get("variance"),
                                    min_val=stats.get("min_val") or stats.get("min"),
                                    max_val=stats.get("max_val") or stats.get("max"),
                                    range_val=stats.get("range_val") or stats.get("range"),
                                    q1=stats.get("q1"),
                                    q2=stats.get("q2"),
                                    q3=stats.get("q3"),
                                    iqr=stats.get("iqr"),
                                    cv=stats.get("cv"),
                                )
                            )

                provenance_items.append(
                    ProvenanceReportItem(
                        section="descriptive_statistics",
                        analysis_id=a.id,
                        analysis_type=a.analysis_type,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        experiment_id=experiment.id,
                        software_version=a.software_version,
                        created_at=a.created_at,
                    )
                )

            elif a.analysis_type.startswith("visualization") or "visualization" in a.analysis_type:
                params = a.parameters or {}
                vis_type = params.get("visualization_type") or a.analysis_type.replace("visualization_", "")
                vis_items.append(
                    VisualizationReportItem(
                        analysis_id=a.id,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        created_at=a.created_at,
                        visualization_type=vis_type,
                        configuration=params,
                    )
                )
                provenance_items.append(
                    ProvenanceReportItem(
                        section="visualizations",
                        analysis_id=a.id,
                        analysis_type=a.analysis_type,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        experiment_id=experiment.id,
                        software_version=a.software_version,
                        created_at=a.created_at,
                    )
                )

            elif (
                "experimental_comparison" in a.analysis_type
                or "statistical" in a.analysis_type
                or a.comparison is not None
            ):
                res = a.result or {}
                stat_res = res.get("statistical_result") or res

                test_name = (
                    stat_res.get("test_name")
                    or stat_res.get("method")
                    or (a.parameters or {}).get("method")
                    or a.analysis_type
                )
                stat_name = stat_res.get("statistic_name") or "statistic"
                stat_val = stat_res.get("statistic_value")
                p_val = stat_res.get("p_value")
                dof = stat_res.get("degrees_of_freedom") or stat_res.get("df")
                eff_name = stat_res.get("effect_size_name") or stat_res.get("effect_size_type")
                eff_val = stat_res.get("effect_size_value") or stat_res.get("effect_size")
                ci = stat_res.get("confidence_interval") or stat_res.get("ci_95")
                is_sig = stat_res.get("is_significant")
                assumption_checks = stat_res.get("assumption_checks") or stat_res.get("assumptions")

                stat_result_items.append(
                    StatisticalResultReportItem(
                        analysis_id=a.id,
                        analysis_type=a.analysis_type,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        comparison_id=a.comparison.id if a.comparison else None,
                        created_at=a.created_at,
                        test_name=str(test_name) if test_name else None,
                        statistic_name=str(stat_name) if stat_name else None,
                        statistic_value=float(stat_val) if stat_val is not None else None,
                        p_value=float(p_val) if p_val is not None else None,
                        degrees_of_freedom=float(dof) if dof is not None else None,
                        effect_size_name=str(eff_name) if eff_name else None,
                        effect_size_value=float(eff_val) if eff_val is not None else None,
                        confidence_interval=[float(x) for x in ci] if isinstance(ci, (list, tuple)) else None,
                        is_significant=bool(is_sig) if is_sig is not None else None,
                        assumption_checks=assumption_checks if isinstance(assumption_checks, dict) else None,
                        raw_result=res,
                    )
                )

                provenance_items.append(
                    ProvenanceReportItem(
                        section="statistical_results",
                        analysis_id=a.id,
                        analysis_type=a.analysis_type,
                        comparison_id=a.comparison.id if a.comparison else None,
                        dataset_id=a.dataset_id,
                        dataset_name=ds_name,
                        experiment_id=experiment.id,
                        software_version=a.software_version,
                        created_at=a.created_at,
                    )
                )

        # 10. Comparisons Section
        comparison_items: list[ComparisonReportItem] = []
        for comp in experiment.comparisons:
            comp_ds_name: str | None = None
            if experiment.dataset_id:
                ds_obj = self.db.scalar(select(Dataset).where(Dataset.id == experiment.dataset_id))
                comp_ds_name = ds_obj.name if ds_obj else None

            stat_method = comp.parameters.get("method") if comp.parameters else None

            comparison_items.append(
                ComparisonReportItem(
                    comparison_id=comp.id,
                    comparison_name=comp.name,
                    comparison_type=comp.comparison_type,
                    dataset_id=experiment.dataset_id,
                    dataset_name=comp_ds_name,
                    group_a_name=comp.group_a.name if comp.group_a else None,
                    group_b_name=comp.group_b.name if comp.group_b else None,
                    group_column=comp.group_column,
                    measurement_column=comp.measurement_column,
                    statistical_method=str(stat_method) if stat_method else None,
                    parameters=comp.parameters or {},
                    created_at=comp.created_at,
                )
            )

            provenance_items.append(
                ProvenanceReportItem(
                    section="comparisons",
                    comparison_id=comp.id,
                    analysis_id=comp.analysis_id,
                    experiment_id=experiment.id,
                    software_version="0.1.0",
                    created_at=comp.created_at,
                )
            )

        return ExperimentReport(
            metadata=header,
            experimental_context=exp_context,
            datasets=dataset_items,
            data_quality=data_quality_items,
            descriptive_statistics=desc_stats_items,
            visualizations=vis_items,
            comparisons=comparison_items,
            statistical_results=stat_result_items,
            provenance=provenance_items,
            generated_at=now_utc,
        )

    def render_markdown(self, report: ExperimentReport) -> str:
        """Renders the structured ExperimentReport DTO into human-readable Markdown text."""
        md: list[str] = []

        m = report.metadata
        md.append(f"# Scientific Report: {m.experiment_name}\n")
        md.append(f"**Report Generated At:** {m.report_generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**Software Version:** {m.software_version}\n")

        # 1. Experiment Overview
        md.append("## 1. Experiment Overview\n")
        md.append(f"- **Experiment ID:** `{m.experiment_id}`")
        md.append(f"- **Name:** {m.experiment_name}")
        md.append(f"- **Status:** `{m.status}`")
        md.append(f"- **Description:** {m.description or 'Not provided'}")
        md.append(f"- **Objective:** {m.objective or 'Not provided'}")
        md.append(f"- **Created At:** {m.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

        # 2. Experimental Context
        c = report.experimental_context
        md.append("## 2. Experimental Context\n")
        md.append(f"- **Organism:** {c.organism or 'Not specified'}")
        md.append(f"- **Condition Type:** {c.condition_type or 'Not specified'}")
        md.append(f"- **Assay Type:** {c.assay_type or 'Not specified'}")
        md.append(f"- **Target Gene:** {c.target_gene or 'Not specified'}")
        md.append(f"- **Notes:** {c.notes or 'None'}\n")

        md.append("### Experimental Groups & Replicates")
        if not c.groups:
            md.append("*No experimental groups defined for this experiment.*\n")
        else:
            md.append("| Group Name | Code | Control? | Description | Replicates Count |")
            md.append("|:---|:---|:---|:---|:---|")
            for g in c.groups:
                ctrl_str = "Yes" if g.is_control else "No"
                md.append(
                    f"| {g.name} | `{g.group_code}` | {ctrl_str} | {g.description or '-'} | {len(g.replicates)} |"
                )
            md.append("")

        # 3. Datasets
        md.append("## 3. Datasets\n")
        if not report.datasets:
            md.append("*No datasets are attached to this experiment.*\n")
        else:
            md.append("| Dataset Name | File Name | Type | Size (Bytes) | Rows | Columns | Validated? |")
            md.append("|:---|:---|:---|:---|:---|:---|:---|")
            for d in report.datasets:
                val_str = "Yes" if d.has_validation else "No"
                row_s = str(d.row_count) if d.row_count is not None else "-"
                col_s = str(d.column_count) if d.column_count is not None else "-"
                line = (
                    f"| {d.dataset_name} | `{d.file_name}` | `{d.file_type}` | "
                    f"{d.file_size:,} | {row_s} | {col_s} | {val_str} |"
                )
                md.append(line)
            md.append("")

        # 4. Data Quality / Validation
        md.append("## 4. Data Quality / Validation\n")
        if not report.data_quality:
            md.append("*No validation or data quality analyses have been recorded yet.*\n")
        else:
            for dq in report.data_quality:
                passed_str = "PASSED" if dq.validation_passed else "WARNINGS / FAILED"
                md.append(f"### Dataset: {dq.dataset_name} (`{dq.analysis_id}`)")
                md.append(f"- **Overall Status:** {passed_str}")
                md.append(f"- **Duplicate Rows:** {dq.duplicate_rows if dq.duplicate_rows is not None else 'N/A'}")
                md.append(f"- **Empty Columns:** {', '.join(dq.empty_columns) if dq.empty_columns else 'None'}")
                if dq.missing_values:
                    md.append(f"- **Missing Values Summary:** `{dq.missing_values}`")
                md.append("")

        # 5. Descriptive Statistics
        md.append("## 5. Descriptive Statistics\n")
        if not report.descriptive_statistics:
            md.append("*No descriptive statistics have been computed for this experiment.*\n")
        else:
            md.append("| Dataset | Column | Count | Mean | Std Dev | Median | IQR | Min | Max |")
            md.append("|:---|:---|:---|:---|:---|:---|:---|:---|:---|")
            for ds in report.descriptive_statistics:
                cnt_s = str(ds.count) if ds.count is not None else "-"
                mean_s = f"{ds.mean:.4f}" if ds.mean is not None else "-"
                std_s = f"{ds.std_dev:.4f}" if ds.std_dev is not None else "-"
                med_s = f"{ds.median:.4f}" if ds.median is not None else "-"
                iqr_s = f"{ds.iqr:.4f}" if ds.iqr is not None else "-"
                min_s = f"{ds.min_val:.4f}" if ds.min_val is not None else "-"
                max_s = f"{ds.max_val:.4f}" if ds.max_val is not None else "-"
                line = (
                    f"| {ds.dataset_name} | `{ds.column_name}` | {cnt_s} | "
                    f"{mean_s} | {std_s} | {med_s} | {iqr_s} | {min_s} | {max_s} |"
                )
                md.append(line)
            md.append("")

        # 6. Visualizations
        md.append("## 6. Visualizations\n")
        if not report.visualizations:
            md.append("*No visualizations have been generated for this experiment.*\n")
        else:
            md.append("| Dataset | Visualization Type | Configuration Summary | Created At |")
            md.append("|:---|:---|:---|:---|")
            for v in report.visualizations:
                ts_str = v.created_at.strftime('%Y-%m-%d %H:%M')
                md.append(
                    f"| {v.dataset_name} | `{v.visualization_type}` | `{v.configuration}` | {ts_str} |"
                )
            md.append("")

        # 7. Experimental Comparisons
        md.append("## 7. Experimental Comparisons\n")
        if not report.comparisons:
            md.append("*No group comparisons have been created for this experiment.*\n")
        else:
            md.append("| Comparison Name | Type | Group A | Group B | Measurement Column | Method |")
            md.append("|:---|:---|:---|:---|:---|:---|")
            for comp in report.comparisons:
                g_a = comp.group_a_name or '-'
                g_b = comp.group_b_name or '-'
                method_s = comp.statistical_method or 'N/A'
                line = (
                    f"| {comp.comparison_name} | `{comp.comparison_type}` | {g_a} | {g_b} | "
                    f"`{comp.measurement_column}` | `{method_s}` |"
                )
                md.append(line)
            md.append("")

        # 8. Statistical Results
        md.append("## 8. Statistical Results\n")
        if not report.statistical_results:
            md.append("*No statistical test results recorded for this experiment.*\n")
        else:
            md.append("| Test / Method | Dataset | Statistic | p-value | Effect Size | Significant? |")
            md.append("|:---|:---|:---|:---|:---|:---|")
            for sr in report.statistical_results:
                test_s = sr.test_name or sr.analysis_type
                stat_val = sr.statistic_value
                stat_str = f"{sr.statistic_name or 'stat'}={stat_val:.4f}" if stat_val is not None else "-"
                pval_str = f"{sr.p_value:.4e}" if sr.p_value is not None else "-"
                eff_val = sr.effect_size_value
                eff_str = f"{sr.effect_size_name or 'effect'}={eff_val:.4f}" if eff_val is not None else "-"
                sig_str = "Yes" if sr.is_significant else ("No" if sr.is_significant is False else "-")
                md.append(
                    f"| `{test_s}` | {sr.dataset_name} | {stat_str} | {pval_str} | {eff_str} | {sig_str} |"
                )
            md.append("")

        # 9. Provenance & Reproducibility
        md.append("## 9. Provenance & Reproducibility\n")
        if not report.provenance:
            md.append("*No analysis provenance items recorded.*\n")
        else:
            md.append("| Section | Analysis ID | Comparison ID | Dataset ID | Software Version | Created At |")
            md.append("|:---|:---|:---|:---|:---|:---|")
            for p in report.provenance:
                an_id = f"`{p.analysis_id}`" if p.analysis_id else "-"
                comp_id = f"`{p.comparison_id}`" if p.comparison_id else "-"
                ds_id = f"`{p.dataset_id}`" if p.dataset_id else "-"
                ts_str = p.created_at.strftime('%Y-%m-%d %H:%M:%S')
                md.append(
                    f"| `{p.section}` | {an_id} | {comp_id} | {ds_id} | `{p.software_version}` | {ts_str} |"
                )
            md.append("")

        # 10. Appendix & Scientific Disclaimer
        md.append("## 10. Appendix & Limitations\n")
        md.append(f"> {report.disclaimer}\n")

        return "\n".join(md)
