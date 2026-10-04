"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  History,
  Download,
  FileCode,
  FileSpreadsheet,
  AlertCircle,
  Info,
  Filter,
  ShieldCheck,
  Calculator,
  FlaskConical,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { Dataset } from "../../../lib/types/dataset";
import {
  ExperimentResultItem,
  ExperimentResultsResponse,
} from "../../../lib/types/results";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import {
  getExperimentResults,
  downloadExperimentResultsExport,
} from "../../../lib/api/experiments";
import { ValidationSummaryCard } from "../../validation/ValidationSummaryCard";
import { ValidationDetailsTabs } from "../../validation/ValidationDetailsTabs";
import { DescriptiveStatisticsCard } from "../../statistics/DescriptiveStatisticsCard";
import { StatisticalResultCard } from "../comparison/StatisticalResultCard";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";

interface ExperimentResultsTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentResultsTab: React.FC<ExperimentResultsTabProps> = ({ workspace }) => {
  const { experiment, attached_datasets } = workspace;

  const [resultsPayload, setResultsPayload] = useState<ExperimentResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string>("all");
  const [selectedDatasetFilter, setSelectedDatasetFilter] = useState<string>("all");
  const [exportingJson, setExportingJson] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);

  const fetchResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getExperimentResults(
        experiment.id,
        selectedTypeFilter !== "all" ? selectedTypeFilter : undefined,
        selectedDatasetFilter !== "all" ? selectedDatasetFilter : undefined
      );
      setResultsPayload(data);
    } catch (err: any) {
      setError(err.detail || "Failed to load experiment scientific results timeline.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [experiment.id, selectedTypeFilter, selectedDatasetFilter]);

  const handleExport = async (format: "json" | "csv") => {
    if (format === "json") setExportingJson(true);
    else setExportingCsv(true);

    try {
      await downloadExperimentResultsExport(experiment.id, format);
    } catch (err: any) {
      alert(`Export failed: ${err.message || "Unable to download export file."}`);
    } finally {
      if (format === "json") setExportingJson(false);
      else setExportingCsv(false);
    }
  };

  const results = resultsPayload?.results || [];

  return (
    <div className="space-y-6">
      {/* Header & Export Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <History className="w-4 h-4 text-cyan-400" />
            <span>Unified Scientific Results & Provenance</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Traceable chronological history of all validation, statistical, and group comparison outputs with full provenance.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("json")}
            disabled={exportingJson || results.length === 0}
          >
            <FileCode className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
            {exportingJson ? "Exporting..." : "Export JSON"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("csv")}
            disabled={exportingCsv || results.length === 0}
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            {exportingCsv ? "Exporting..." : "Export CSV Index"}
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold text-slate-300">Analysis Type:</span>
            <select
              value={selectedTypeFilter}
              onChange={(e) => setSelectedTypeFilter(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Types</option>
              <option value="validation">Data Quality Validation</option>
              <option value="descriptive_statistics">Descriptive Statistics</option>
              <option value="experimental_comparison">Group Comparisons</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">Dataset:</span>
            <select
              value={selectedDatasetFilter}
              onChange={(e) => setSelectedDatasetFilter(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Datasets</option>
              {attached_datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name || ds.file_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-slate-400 font-mono text-[11px]">
          Total Persisted Analyses: <strong className="text-slate-200">{results.length}</strong>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchResults}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry
          </Button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading ? (
        <div className="space-y-4">
          <div className="h-32 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse" />
          <div className="h-32 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse" />
        </div>
      ) : results.length === 0 ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800 space-y-3">
          <History className="w-10 h-10 text-slate-600 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-300">No Scientific Results Persisted Yet</h4>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Execute data quality validation, calculate descriptive statistics, or run group comparisons to generate traceable scientific results in this timeline.
          </p>
        </Card>
      ) : (
        /* Results Timeline */
        <div className="space-y-8">
          {results.map((item) => {
            const isValidation = item.analysis_type === "validation";
            const isStats = item.analysis_type === "descriptive_statistics";
            const isComparison = item.analysis_type.includes("experimental_comparison");

            return (
              <Card
                key={item.analysis_id}
                className="p-6 bg-slate-900/70 border-slate-800 shadow-xl space-y-6"
              >
                {/* Result Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-cyan-400">
                      {isValidation ? (
                        <ShieldCheck className="w-5 h-5" />
                      ) : isStats ? (
                        <Calculator className="w-5 h-5" />
                      ) : (
                        <FlaskConical className="w-5 h-5" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                          {isValidation
                            ? "Data Quality Validation Report"
                            : isStats
                            ? "Descriptive Statistics Report"
                            : item.comparison?.name || "Experimental Group Comparison"}
                        </h4>
                        <Badge variant={isValidation ? "pass" : isStats ? "info" : "warning"}>
                          {isValidation ? "Module 2" : isStats ? "Module 3" : "Module 6"}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Executed on <strong className="text-slate-300">{item.dataset.name}</strong> ({item.dataset.file_name})
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 text-xs text-slate-400 self-end sm:self-center">
                    <span className="font-mono text-[11px]">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                    <Link href={`/datasets/${item.dataset.id}`} passHref>
                      <Button variant="outline" size="sm">
                        <ExternalLink className="w-3.5 h-3.5 mr-1" />
                        Inspect Dataset
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Render Scientific Output */}
                <div>
                  {isValidation && item.result.summary && (
                    <div className="space-y-6">
                      <ValidationSummaryCard validation={item.result as any} />
                      <ValidationDetailsTabs validation={item.result as any} />
                    </div>
                  )}

                  {isStats && item.result.statistics && (
                    <DescriptiveStatisticsCard report={item.result as any} />
                  )}

                  {isComparison && (
                    <StatisticalResultCard
                      comparison={{
                        id: item.analysis_id,
                        experiment_id: item.experiment.id,
                        analysis_id: item.analysis_id,
                        name: item.comparison?.name || item.analysis_type,
                        comparison_type: item.comparison?.comparison_type || "two_group",
                        measurement_column: item.comparison?.measurement_column || "",
                        group_column: item.comparison?.group_column || null,
                        parameters: item.parameters,
                        result_summary: item.result,
                        created_at: item.created_at,
                      }}
                    />
                  )}
                </div>

                {/* Provenance Card */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400 font-mono">
                  <div className="flex flex-wrap items-center gap-2">
                    <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                    <span>Analysis ID: <code className="text-cyan-300">{item.analysis_id}</code></span>
                    <span>•</span>
                    <span>Dataset ID: <code className="text-slate-300">{item.dataset.id}</code></span>
                    <span>•</span>
                    <span>Experiment ID: <code className="text-slate-300">{item.experiment.id}</code></span>
                  </div>
                  <div className="flex items-center space-x-3 text-slate-400 font-sans">
                    <span>Software Version: <strong className="text-slate-300">{item.software_version}</strong></span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
