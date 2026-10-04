"use client";

import React, { useEffect, useState } from "react";
import {
  FileText,
  FileCode,
  Download,
  AlertCircle,
  RefreshCw,
  Info,
  CheckCircle2,
  Database,
  ShieldCheck,
  Calculator,
  FlaskConical,
  GitCompare,
  History,
  Layers,
  FileSpreadsheet,
} from "lucide-react";
import { ExperimentReport } from "../../../lib/types/report";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import {
  getExperimentReport,
  downloadExperimentReportExport,
} from "../../../lib/api/experiments";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";

interface ExperimentReportTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentReportTab: React.FC<ExperimentReportTabProps> = ({ workspace }) => {
  const { experiment } = workspace;

  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [markdownText, setMarkdownText] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<"structured" | "markdown">("structured");
  const [exportingJson, setExportingJson] = useState(false);
  const [exportingMd, setExportingMd] = useState(false);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [jsonRes, mdRes] = await Promise.all([
        getExperimentReport(experiment.id, "json") as Promise<ExperimentReport>,
        getExperimentReport(experiment.id, "markdown") as Promise<string>,
      ]);
      setReport(jsonRes);
      setMarkdownText(mdRes);
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to load scientific report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [experiment.id]);

  const handleExport = async (format: "json" | "markdown") => {
    if (format === "json") setExportingJson(true);
    else setExportingMd(true);

    try {
      await downloadExperimentReportExport(experiment.id, format);
    } catch (err: any) {
      alert(`Export failed: ${err.message || "Unable to download report file."}`);
    } finally {
      if (format === "json") setExportingJson(false);
      else setExportingMd(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-24 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse" />
        <div className="h-64 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <Card className="p-6 bg-slate-900/60 border-slate-800 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-200">Unable to Generate Report</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchReportData}>
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry
        </Button>
      </Card>
    );
  }

  const { metadata, experimental_context, datasets, data_quality, descriptive_statistics, visualizations, comparisons, statistical_results, provenance, disclaimer } = report;

  return (
    <div className="space-y-6">
      {/* Header & Export Actions Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <FileText className="w-4.5 h-4.5 text-cyan-400" />
            <span>Scientific Experiment Report</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic summary assembled from recorded experimental context, datasets, validation, statistics, and provenance.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center bg-slate-900 p-1 rounded-lg border border-slate-800 mr-2 text-xs">
            <button
              onClick={() => setViewMode("structured")}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                viewMode === "structured"
                  ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Structured View
            </button>
            <button
              onClick={() => setViewMode("markdown")}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                viewMode === "markdown"
                  ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Markdown View
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("json")}
            disabled={exportingJson}
          >
            <FileCode className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
            {exportingJson ? "Exporting..." : "Export JSON"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("markdown")}
            disabled={exportingMd}
          >
            <Download className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            {exportingMd ? "Exporting..." : "Export Markdown"}
          </Button>
        </div>
      </div>

      {viewMode === "markdown" ? (
        /* Markdown Preview View */
        <Card className="p-6 bg-slate-950 border-slate-800 font-mono text-xs text-slate-300 space-y-4 overflow-x-auto">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-slate-400 text-[11px]">
            <span>RENDERED MARKDOWN REPORT PREVIEW</span>
            <span>Version: {metadata.software_version}</span>
          </div>
          <pre className="whitespace-pre-wrap leading-relaxed font-mono text-slate-300">{markdownText}</pre>
        </Card>
      ) : (
        /* Structured Report Sections */
        <div className="space-y-6">

          {/* 1. Experiment Overview */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>1. Experiment Overview</span>
              </h4>
              <Badge variant="info">{metadata.status}</Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block">Experiment Name</span>
                <span className="font-semibold text-slate-100 text-sm">{metadata.experiment_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Experiment ID</span>
                <code className="font-mono text-cyan-300 text-xs">{metadata.experiment_id}</code>
              </div>
              <div>
                <span className="text-slate-400 block">Objective</span>
                <span className="text-slate-200">{metadata.objective || "Not provided"}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Description</span>
                <span className="text-slate-200">{metadata.description || "Not provided"}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Report Generated At</span>
                <span className="font-mono text-slate-300">{new Date(report.generated_at).toUTCString()}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Software Version</span>
                <span className="font-mono text-slate-300">{metadata.software_version}</span>
              </div>
            </div>
          </Card>

          {/* 2. Experimental Context */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <FlaskConical className="w-4 h-4 text-emerald-400" />
              <span>2. Experimental Context & Groups</span>
            </h4>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800/80">
              <div>
                <span className="text-slate-400 block">Organism</span>
                <span className="font-medium text-slate-200">{experimental_context.organism || "Not specified"}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Condition Type</span>
                <span className="font-medium text-slate-200">{experimental_context.condition_type || "Not specified"}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Assay Type</span>
                <span className="font-medium text-slate-200">{experimental_context.assay_type || "Not specified"}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Target Gene</span>
                <span className="font-medium text-slate-200">{experimental_context.target_gene || "Not specified"}</span>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-slate-300">Experimental Groups ({experimental_context.groups.length})</h5>
              {experimental_context.groups.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No experimental groups defined for this experiment.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="py-2 px-3 font-semibold">Group Name</th>
                        <th className="py-2 px-3 font-semibold">Code</th>
                        <th className="py-2 px-3 font-semibold">Control?</th>
                        <th className="py-2 px-3 font-semibold">Description</th>
                        <th className="py-2 px-3 font-semibold">Replicates</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {experimental_context.groups.map((g) => (
                        <tr key={g.id}>
                          <td className="py-2 px-3 font-medium text-slate-200">{g.name}</td>
                          <td className="py-2 px-3 font-mono text-cyan-300">{g.group_code}</td>
                          <td className="py-2 px-3">{g.is_control ? <Badge variant="pass">Yes</Badge> : "No"}</td>
                          <td className="py-2 px-3 text-slate-400">{g.description || "-"}</td>
                          <td className="py-2 px-3 font-mono">{g.replicates.length}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>

          {/* 3. Datasets */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Database className="w-4 h-4 text-cyan-400" />
              <span>3. Attached Datasets ({datasets.length})</span>
            </h4>

            {datasets.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No datasets attached to this experiment.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2 px-3 font-semibold">Dataset Name</th>
                      <th className="py-2 px-3 font-semibold">File Name</th>
                      <th className="py-2 px-3 font-semibold">Type</th>
                      <th className="py-2 px-3 font-semibold">Size</th>
                      <th className="py-2 px-3 font-semibold">Rows</th>
                      <th className="py-2 px-3 font-semibold">Cols</th>
                      <th className="py-2 px-3 font-semibold">Validation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {datasets.map((d) => (
                      <tr key={d.dataset_id}>
                        <td className="py-2 px-3 font-medium text-slate-200">{d.dataset_name}</td>
                        <td className="py-2 px-3 font-mono text-slate-400">{d.file_name}</td>
                        <td className="py-2 px-3 font-mono uppercase text-cyan-400">{d.file_type}</td>
                        <td className="py-2 px-3 font-mono">{d.file_size.toLocaleString()} B</td>
                        <td className="py-2 px-3 font-mono">{d.row_count ?? "-"}</td>
                        <td className="py-2 px-3 font-mono">{d.column_count ?? "-"}</td>
                        <td className="py-2 px-3">
                          {d.has_validation ? <Badge variant="pass">Validated</Badge> : <Badge variant="neutral">Not Run</Badge>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* 4. Data Quality / Validation */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>4. Data Quality / Validation Findings ({data_quality.length})</span>
            </h4>

            {data_quality.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No validation or data quality analyses have been recorded yet.</p>
            ) : (
              <div className="space-y-4">
                {data_quality.map((dq) => (
                  <div key={dq.analysis_id} className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{dq.dataset_name}</span>
                      <Badge variant={dq.validation_passed ? "pass" : "warning"}>
                        {dq.validation_passed ? "Validation Passed" : "Warnings Present"}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] text-slate-400">
                      <div>Duplicate Rows: <strong className="text-slate-200">{dq.duplicate_rows ?? "N/A"}</strong></div>
                      <div>Empty Columns: <strong className="text-slate-200">{dq.empty_columns?.length || 0}</strong></div>
                      <div className="col-span-2">Analysis ID: <code className="text-cyan-300">{dq.analysis_id}</code></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* 5. Descriptive Statistics */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Calculator className="w-4 h-4 text-cyan-400" />
              <span>5. Descriptive Statistics ({descriptive_statistics.length} Columns)</span>
            </h4>

            {descriptive_statistics.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No descriptive statistics have been computed for this experiment.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-2 px-3 font-semibold">Dataset</th>
                      <th className="py-2 px-3 font-semibold">Column</th>
                      <th className="py-2 px-3 font-semibold">Count</th>
                      <th className="py-2 px-3 font-semibold">Mean</th>
                      <th className="py-2 px-3 font-semibold">Std Dev</th>
                      <th className="py-2 px-3 font-semibold">Median</th>
                      <th className="py-2 px-3 font-semibold">IQR</th>
                      <th className="py-2 px-3 font-semibold">Min</th>
                      <th className="py-2 px-3 font-semibold">Max</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300 text-[11px]">
                    {descriptive_statistics.map((ds, idx) => (
                      <tr key={idx}>
                        <td className="py-2 px-3 text-slate-400 font-sans">{ds.dataset_name}</td>
                        <td className="py-2 px-3 font-bold text-cyan-300 font-sans">{ds.column_name}</td>
                        <td className="py-2 px-3">{ds.count ?? "-"}</td>
                        <td className="py-2 px-3">{ds.mean !== null ? ds.mean.toFixed(4) : "-"}</td>
                        <td className="py-2 px-3">{ds.std_dev !== null ? ds.std_dev.toFixed(4) : "-"}</td>
                        <td className="py-2 px-3">{ds.median !== null ? ds.median.toFixed(4) : "-"}</td>
                        <td className="py-2 px-3">{ds.iqr !== null ? ds.iqr.toFixed(4) : "-"}</td>
                        <td className="py-2 px-3">{ds.min_val !== null ? ds.min_val.toFixed(4) : "-"}</td>
                        <td className="py-2 px-3">{ds.max_val !== null ? ds.max_val.toFixed(4) : "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* 6. Visualizations & 7. Comparisons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
                <FileSpreadsheet className="w-4 h-4 text-purple-400" />
                <span>6. Visualizations ({visualizations.length})</span>
              </h4>
              {visualizations.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No visualizations recorded for this experiment.</p>
              ) : (
                <div className="space-y-2 text-xs">
                  {visualizations.map((v) => (
                    <div key={v.analysis_id} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                      <div>
                        <span className="font-semibold text-slate-200 capitalize">{v.visualization_type}</span>
                        <span className="text-slate-400 text-[11px] block">{v.dataset_name}</span>
                      </div>
                      <Badge variant="info">Configured</Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
                <GitCompare className="w-4 h-4 text-amber-400" />
                <span>7. Experimental Comparisons ({comparisons.length})</span>
              </h4>
              {comparisons.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No group comparisons recorded.</p>
              ) : (
                <div className="space-y-2 text-xs">
                  {comparisons.map((c) => (
                    <div key={c.comparison_id} className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                      <div className="flex justify-between font-semibold text-slate-200">
                        <span>{c.comparison_name}</span>
                        <span className="font-mono text-cyan-400 text-[11px]">{c.statistical_method || c.comparison_type}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 flex justify-between">
                        <span>Group A: {c.group_a_name || "-"}</span>
                        <span>Group B: {c.group_b_name || "-"}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* 8. Statistical Results */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <FlaskConical className="w-4 h-4 text-cyan-400" />
              <span>8. Statistical Test Results ({statistical_results.length})</span>
            </h4>

            {statistical_results.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No statistical test results recorded for this experiment.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-2 px-3 font-semibold">Test / Method</th>
                      <th className="py-2 px-3 font-semibold">Dataset</th>
                      <th className="py-2 px-3 font-semibold">Statistic</th>
                      <th className="py-2 px-3 font-semibold">p-value</th>
                      <th className="py-2 px-3 font-semibold">Effect Size</th>
                      <th className="py-2 px-3 font-semibold">Significance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300 text-[11px]">
                    {statistical_results.map((sr) => (
                      <tr key={sr.analysis_id}>
                        <td className="py-2 px-3 font-sans font-bold text-slate-200">{sr.test_name || sr.analysis_type}</td>
                        <td className="py-2 px-3 font-sans text-slate-400">{sr.dataset_name}</td>
                        <td className="py-2 px-3">{sr.statistic_value !== null ? `${sr.statistic_name || 'stat'}: ${sr.statistic_value.toFixed(4)}` : "-"}</td>
                        <td className="py-2 px-3 text-cyan-300">{sr.p_value !== null ? sr.p_value.toExponential(4) : "-"}</td>
                        <td className="py-2 px-3">{sr.effect_size_value !== null ? `${sr.effect_size_name || 'effect'}: ${sr.effect_size_value.toFixed(4)}` : "-"}</td>
                        <td className="py-2 px-3 font-sans">
                          {sr.is_significant ? <Badge variant="pass">Significant</Badge> : <Badge variant="neutral">Not Significant</Badge>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* 9. Provenance & Traceability */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <History className="w-4 h-4 text-slate-400" />
              <span>9. Provenance & Traceability Index ({provenance.length} Items)</span>
            </h4>

            {provenance.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No provenance items recorded.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-2 px-3 font-semibold">Section</th>
                      <th className="py-2 px-3 font-semibold">Analysis ID</th>
                      <th className="py-2 px-3 font-semibold">Comparison ID</th>
                      <th className="py-2 px-3 font-semibold">Dataset ID</th>
                      <th className="py-2 px-3 font-semibold">Software Version</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px] text-slate-400">
                    {provenance.map((p, idx) => (
                      <tr key={idx}>
                        <td className="py-2 px-3 font-sans text-cyan-400 capitalize">{p.section}</td>
                        <td className="py-2 px-3 text-slate-300">{p.analysis_id || "-"}</td>
                        <td className="py-2 px-3 text-slate-300">{p.comparison_id || "-"}</td>
                        <td className="py-2 px-3 text-slate-300">{p.dataset_id || "-"}</td>
                        <td className="py-2 px-3 text-slate-400">{p.software_version}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* 10. Appendix / Disclaimer */}
          <Card className="p-4 bg-amber-500/10 border-amber-500/20 text-amber-300 text-xs flex items-start space-x-3">
            <Info className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
            <div>
              <strong className="font-semibold block text-amber-200 mb-0.5">Scientific Interpretation Notice</strong>
              <p className="text-amber-300/90 leading-relaxed">{disclaimer}</p>
            </div>
          </Card>

        </div>
      )}
    </div>
  );
};
