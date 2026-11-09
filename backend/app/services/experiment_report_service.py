from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ExperimentNotFoundError
from app.models.analysis import Analysis
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.experimental_group import ExperimentalGroup
from app.models.factorial_comparison import FactorialComparison
from app.schemas.report import (
    AnovaEffectReportItem,
    ComparisonReportItem,
    DataQualityReportItem,
    DatasetReportItem,
    DescriptiveStatisticsReportItem,
    ExperimentalContextReport,
    ExperimentalGroupReportItem,
    ExperimentReport,
    ExperimentReportHeader,
    FactorialAnalysisReportItem,
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
                        confidence_interval=[float(x) for x in ci] if isinstance(ci, list | tuple) else None,
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

        # 11. Two-Way Factorial Analyses (Module 9)
        fcomp_stmt = (
            select(FactorialComparison)
            .options(
                joinedload(FactorialComparison.dataset),
                joinedload(FactorialComparison.factor_a),
                joinedload(FactorialComparison.factor_b),
            )
            .where(FactorialComparison.experiment_id == experiment_id)
            .order_by(FactorialComparison.created_at.desc())
        )
        factorial_comparisons = list(self.db.scalars(fcomp_stmt).unique().all())

        factorial_items: list[FactorialAnalysisReportItem] = []
        for fc in factorial_comparisons:
            res = fc.result_summary or {}
            params = fc.parameters or {}

            ds_name = fc.dataset.name if fc.dataset else None
            if not ds_name and fc.dataset_id:
                ds_match = next((d.dataset_name for d in dataset_items if d.dataset_id == fc.dataset_id), None)
                ds_name = ds_match or "Attached Dataset"

            effects_raw = res.get("effects") or {}
            effects_list: list[AnovaEffectReportItem] = []
            if isinstance(effects_raw, dict):
                for eff_key, eff_data in effects_raw.items():
                    if isinstance(eff_data, dict):
                        effects_list.append(
                            AnovaEffectReportItem(
                                effect_name=eff_data.get("effect_name", eff_key),
                                df=float(eff_data.get("df", 0.0)),
                                sum_sq=float(eff_data.get("sum_sq", 0.0)),
                                mean_sq=float(eff_data["mean_sq"]) if eff_data.get("mean_sq") is not None else None,
                                f_statistic=float(eff_data["f_statistic"])
                                if eff_data.get("f_statistic") is not None
                                else None,
                                p_value=float(eff_data["p_value"]) if eff_data.get("p_value") is not None else None,
                                is_significant=bool(eff_data.get("is_significant", False)),
                                partial_eta_squared=float(eff_data["partial_eta_squared"])
                                if eff_data.get("partial_eta_squared") is not None
                                else None,
                                partial_eta_squared_ci=[float(x) for x in eff_data["partial_eta_squared_ci"]]
                                if isinstance(eff_data.get("partial_eta_squared_ci"), list | tuple)
                                else None,
                                effect_size_interpretation=eff_data.get("effect_size_interpretation"),
                            )
                        )

            alpha_val = float(params.get("alpha") or res.get("alpha") or 0.05)
            post_hoc_val = str(params.get("post_hoc_method") or res.get("post_hoc_method") or "tukey")
            coding_val = str(params.get("contrast_coding") or res.get("contrast_coding") or "sum-to-zero (deviation)")
            anova_type_val = str(res.get("anova_type") or "Type III")

            raw_assumptions = res.get("assumptions") or []
            assumptions_val: list[dict[str, Any]] = []
            if isinstance(raw_assumptions, list):
                for asm in raw_assumptions:
                    if isinstance(asm, dict):
                        tname = asm.get("name") or asm.get("test_name") or "Assumption"
                        is_p = asm.get("passed") if "passed" in asm else asm.get("is_valid", False)
                        dtls = asm.get("details") or asm.get("warning_message") or ""
                        assumptions_val.append(
                            {
                                **asm,
                                "name": tname,
                                "test_name": tname,
                                "passed": is_p,
                                "is_valid": is_p,
                                "details": dtls,
                                "warning_message": dtls,
                            }
                        )

            post_hoc_comps = res.get("post_hoc_comparisons") or []
            if not isinstance(post_hoc_comps, list):
                post_hoc_comps = []

            simple_effs = res.get("simple_effects") or []
            if not isinstance(simple_effs, list):
                simple_effs = []

            warnings_val = res.get("warnings") or []
            if not isinstance(warnings_val, list):
                warnings_val = []

            factorial_items.append(
                FactorialAnalysisReportItem(
                    comparison_id=fc.id,
                    analysis_id=fc.analysis_id,
                    comparison_name=fc.name,
                    description=fc.description,
                    status=fc.status,
                    created_at=fc.created_at,
                    dataset_id=fc.dataset_id,
                    dataset_name=ds_name,
                    factor_a_id=fc.factor_a_id,
                    factor_a_name=fc.factor_a.name if fc.factor_a else None,
                    factor_a_column=fc.factor_a_column,
                    factor_b_id=fc.factor_b_id,
                    factor_b_name=fc.factor_b.name if fc.factor_b else None,
                    factor_b_column=fc.factor_b_column,
                    measurement_column=fc.measurement_column,
                    alpha=alpha_val,
                    post_hoc_method=post_hoc_val,
                    contrast_coding=coding_val,
                    anova_type=anova_type_val,
                    model_formula=res.get("model_formula"),
                    total_rows_input=res.get("total_rows_input"),
                    valid_rows_used=res.get("valid_rows_used"),
                    excluded_rows_count=res.get("excluded_rows_count"),
                    exclusion_reasons=res.get("exclusion_reasons")
                    if isinstance(res.get("exclusion_reasons"), dict)
                    else {},
                    design_balance=res.get("design_balance"),
                    is_balanced=res.get("is_balanced"),
                    cell_sample_sizes=res.get("cell_sample_sizes")
                    if isinstance(res.get("cell_sample_sizes"), dict)
                    else {},
                    effects=effects_list,
                    interaction_significant=bool(res.get("interaction_significant", False)),
                    assumptions=assumptions_val,
                    post_hoc_comparisons=post_hoc_comps,
                    simple_effects=simple_effs,
                    warnings=warnings_val,
                    scientific_statement=res.get("scientific_statement"),
                    parameters=params,
                    raw_result=res,
                )
            )

            provenance_items.append(
                ProvenanceReportItem(
                    section="factorial_analyses",
                    comparison_id=fc.id,
                    analysis_id=fc.analysis_id,
                    dataset_id=fc.dataset_id,
                    dataset_name=ds_name,
                    experiment_id=experiment.id,
                    software_version="0.1.0",
                    created_at=fc.created_at,
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
            factorial_analyses=factorial_items,
            statistical_results=stat_result_items,
            provenance=provenance_items,
            generated_at=now_utc,
        )

    def render_markdown(self, report: ExperimentReport) -> str:
        """Renders the structured ExperimentReport DTO into human-readable Markdown text."""
        md: list[str] = []

        def _fmt_p(p: float | None) -> str:
            if p is None:
                return "-"
            if p < 0.0001:
                return "< 0.0001"
            return f"{p:.4f}"

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
                pval_str = _fmt_p(sr.p_value)
                eff_val = sr.effect_size_value
                eff_str = f"{sr.effect_size_name or 'effect'}={eff_val:.4f}" if eff_val is not None else "-"
                sig_str = "Yes" if sr.is_significant else ("No" if sr.is_significant is False else "-")
                md.append(
                    f"| `{test_s}` | {sr.dataset_name} | {stat_str} | {pval_str} | {eff_str} | {sig_str} |"
                )
            md.append("")

        # 9. Two-Way Factorial Analyses (Module 9)
        md.append("## 9. Two-Way Factorial Analyses\n")
        if not report.factorial_analyses:
            md.append("*No two-way factorial analyses recorded for this experiment.*\n")
        else:
            for fa in report.factorial_analyses:
                md.append(f"### Factorial Comparison: {fa.comparison_name} (`{fa.comparison_id}`)\n")
                if fa.description:
                    md.append(f"*{fa.description}*\n")

                md.append(f"- **Dataset:** {fa.dataset_name or 'N/A'} (ID: `{fa.dataset_id or 'None'}`)")
                if fa.analysis_id:
                    md.append(f"- **Analysis Record ID:** `{fa.analysis_id}`")
                f_a_display = (
                    f"{fa.factor_a_name} (`{fa.factor_a_column}`)"
                    if fa.factor_a_name
                    else f"`{fa.factor_a_column}`"
                )
                f_b_display = (
                    f"{fa.factor_b_name} (`{fa.factor_b_column}`)"
                    if fa.factor_b_name
                    else f"`{fa.factor_b_column}`"
                )
                md.append(f"- **Factor A:** {f_a_display}")
                md.append(f"- **Factor B:** {f_b_display}")
                md.append(f"- **Measurement / Response Column:** `{fa.measurement_column}`")
                md.append(f"- **Model Formula:** `{fa.model_formula or 'Two-Factor Full Factorial'}`")
                md.append(f"- **ANOVA Type:** {fa.anova_type} (Contrasts: {fa.contrast_coding})")
                md.append(f"- **Significance Threshold (α):** {fa.alpha}")
                md.append(f"- **Post-Hoc Adjustment:** {fa.post_hoc_method.title()}")
                bal_str = fa.design_balance.title() if fa.design_balance else "Unknown"
                md.append(
                    f"- **Design Balance:** {bal_str} (Input Rows: {fa.total_rows_input or '-'}, "
                    f"Valid Used: {fa.valid_rows_used or '-'}, Excluded: {fa.excluded_rows_count or 0})"
                )
                if fa.exclusion_reasons:
                    reasons_str = ", ".join(
                        f"{k}: {v}" for k, v in fa.exclusion_reasons.items() if v > 0
                    )
                    if reasons_str:
                        md.append(f"- **Exclusion Accounting:** {reasons_str}")
                md.append("")

                # ANOVA Table
                md.append("#### Type III ANOVA Table")
                if not fa.effects:
                    md.append("*No effect results available.*")
                else:
                    md.append(
                        "| Effect | Sum of Sq | df | Mean Sq | F-statistic | p-value | Partial η² [95% CI] | Sig? |"
                    )
                    md.append("|:---|:---|:---|:---|:---|:---|:---|:---|")
                    for eff in fa.effects:
                        ss_s = f"{eff.sum_sq:.4f}"
                        df_s = f"{eff.df:.1f}" if eff.df.is_integer() else f"{eff.df:.2f}"
                        ms_s = f"{eff.mean_sq:.4f}" if eff.mean_sq is not None else "-"
                        f_s = f"{eff.f_statistic:.4f}" if eff.f_statistic is not None else "-"
                        p_s = _fmt_p(eff.p_value)
                        if eff.partial_eta_squared is not None:
                            if eff.partial_eta_squared_ci and len(eff.partial_eta_squared_ci) == 2:
                                eta_s = (
                                    f"{eff.partial_eta_squared:.4f} "
                                    f"[{eff.partial_eta_squared_ci[0]:.3f}, {eff.partial_eta_squared_ci[1]:.3f}]"
                                )
                            else:
                                eta_s = f"{eff.partial_eta_squared:.4f}"
                        else:
                            eta_s = "-"
                        sig_s = "Yes" if eff.is_significant else "No"
                        md.append(
                            f"| **{eff.effect_name}** | {ss_s} | {df_s} | {ms_s} | {f_s} | {p_s} | {eta_s} | {sig_s} |"
                        )
                md.append("")

                # Interaction & Conditional Breakdown
                md.append("#### Interaction Assessment & Interpretation")
                if fa.interaction_significant:
                    md.append(
                        "> **Significant Interaction Detected:** The interaction between Factor A and Factor B is "
                        "statistically significant (p < α). Because the effect of one factor varies across levels "
                        "of the other, marginal main effects can be misleading. "
                        "Conditional simple main effects are reported below:\n"
                    )
                    if fa.simple_effects:
                        md.append(
                            "| Slice Factor | Level | Target Factor | F-stat | df (num/den) | p-value | Sig? |"
                        )
                        md.append("|:---|:---|:---|:---|:---|:---|:---|")
                        for se in fa.simple_effects:
                            f_val = se.get("f_statistic")
                            f_str = f"{f_val:.4f}" if f_val is not None else "-"
                            df_b = se.get("df_between")
                            df_w = se.get("df_within")
                            df_str = (
                                f"{df_b:.0f}/{df_w:.0f}"
                                if (df_b is not None and df_w is not None)
                                else "-"
                            )
                            p_val = se.get("p_value")
                            p_str = _fmt_p(p_val)
                            sig_str = "Yes" if se.get("is_significant") else "No"
                            md.append(
                                f"| `{se.get('slice_factor')}` | `{se.get('slice_level')}` | "
                                f"`{se.get('target_factor')}` | {f_str} | {df_str} | {p_str} | {sig_str} |"
                            )
                        md.append("")
                else:
                    md.append(
                        "> **No Significant Interaction:** The Factor A × Factor B interaction is not statistically "
                        "significant (p ≥ α). Main effects can be interpreted across levels of the other factor.\n"
                    )
                    if fa.post_hoc_comparisons:
                        md.append(
                            f"##### Marginal Post-Hoc Pairwise Comparisons ({fa.post_hoc_method.title()})"
                        )
                        md.append(
                            "| Factor | Comparison | Mean Diff | Adjusted p-value | 95% CI | Significant? |"
                        )
                        md.append("|:---|:---|:---|:---|:---|:---|")
                        for ph in fa.post_hoc_comparisons:
                            fac = ph.get("factor", "-")
                            g1 = ph.get("group1", "")
                            g2 = ph.get("group2", "")
                            diff = ph.get("mean_difference")
                            diff_s = f"{diff:.4f}" if diff is not None else "-"
                            p_val = ph.get("p_value_adjusted") or ph.get("p_value")
                            p_s = _fmt_p(p_val)
                            ci = ph.get("ci_95") or ph.get("confidence_interval")
                            ci_s = (
                                f"[{ci[0]:.3f}, {ci[1]:.3f}]"
                                if (isinstance(ci, list | tuple) and len(ci) == 2)
                                else "-"
                            )
                            sig_s = "Yes" if ph.get("is_significant") else "No"
                            md.append(
                                f"| `{fac}` | `{g1} vs {g2}` | {diff_s} | {p_s} | {ci_s} | {sig_s} |"
                            )
                        md.append("")

                # Assumption Diagnostics
                if fa.assumptions:
                    md.append("#### Model Assumption Diagnostics")
                    md.append(
                        "| Assumption Test | Statistic | p-value | Assessment | Details / Guidance |"
                    )
                    md.append("|:---|:---|:---|:---|:---|")
                    for asm in fa.assumptions:
                        tname = asm.get("name") or asm.get("test_name", "Test")
                        st = asm.get("statistic")
                        st_s = f"{st:.4f}" if st is not None else "-"
                        pv = asm.get("p_value")
                        pv_s = _fmt_p(pv)
                        is_v = asm.get("passed") if "passed" in asm else asm.get("is_valid", False)
                        status_s = "No violation detected" if is_v else "Violation detected"
                        warn = asm.get("details") or asm.get("warning_message") or (
                            "No evidence of violation"
                            if is_v
                            else "Potential departure from assumption"
                        )
                        md.append(f"| {tname} | {st_s} | {pv_s} | {status_s} | {warn} |")
                    md.append(
                        "\n> *Note: Diagnostic tests evaluate departure from standard ANOVA assumptions "
                        "but do not prove that underlying distributional assumptions are strictly met. "
                        "Interpretation should consider experimental design and biological sample size.*\n"
                    )

                # Cell Sample Sizes
                if fa.cell_sample_sizes:
                    md.append("#### Factorial Design Cell Sample Sizes")
                    md.append("| Cell (Factor A × Factor B) | Replicates (N) |")
                    md.append("|:---|:---|")
                    for cell_k, cell_n in sorted(fa.cell_sample_sizes.items()):
                        md.append(f"| `{cell_k}` | {cell_n} |")
                    md.append("")

                # Scientific Statement
                if fa.scientific_statement:
                    md.append("#### Scientific Statement")
                    md.append(f"> {fa.scientific_statement}\n")

                # Warnings
                if fa.warnings:
                    md.append("#### Warnings & Analysis Limitations")
                    for w in fa.warnings:
                        md.append(f"- ⚠️ {w}")
                    md.append("")

                md.append(
                    f"*Provenance: Analysis Record `{fa.analysis_id or 'None'}`, Comparison `{fa.comparison_id}`, "
                    f"created at {fa.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}.*\n"
                )

        # 10. Provenance & Reproducibility
        md.append("## 10. Provenance & Reproducibility\n")
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

        # 11. Appendix & Scientific Disclaimer
        md.append("## 11. Appendix & Limitations\n")
        md.append(f"> {report.disclaimer}\n")

        return "\n".join(md)
