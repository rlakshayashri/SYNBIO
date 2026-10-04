"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calculator,
  Play,
  AlertCircle,
  ExternalLink,
  FileSpreadsheet,
  Info,
} from "lucide-react";
import { Dataset } from "../../../lib/types/dataset";
import { DescriptiveStatisticsResult } from "../../../lib/types/statistics";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { calculateDescriptiveStatistics } from "../../../lib/api/statistics";
import { DescriptiveStatisticsCard } from "../../statistics/DescriptiveStatisticsCard";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";

interface ExperimentStatisticsTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentStatisticsTab: React.FC<ExperimentStatisticsTabProps> = ({ workspace }) => {
  const { experiment, attached_datasets } = workspace;

  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [statistics, setStatistics] = useState<DescriptiveStatisticsResult | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync selected dataset when attached datasets change
  useEffect(() => {
    if (attached_datasets.length > 0) {
      if (!selectedDatasetId || !attached_datasets.some((d) => d.id === selectedDatasetId)) {
        setSelectedDatasetId(attached_datasets[0].id);
        setStatistics(null);
      }
    } else {
      setSelectedDatasetId("");
      setStatistics(null);
    }
  }, [attached_datasets]);

  const selectedDataset = attached_datasets.find((d) => d.id === selectedDatasetId);

  const handleCalculateStatistics = async () => {
    if (!selectedDatasetId) return;

    setCalculating(true);
    setError(null);

    try {
      const result = await calculateDescriptiveStatistics(selectedDatasetId);
      setStatistics(result);
    } catch (err: any) {
      setError(err.detail || "Descriptive statistics calculation failed. Please try again.");
    } finally {
      setCalculating(false);
    }
  };

  if (attached_datasets.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <Calculator className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Attached Datasets</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No datasets are attached to this experiment yet. Attach a dataset from the Datasets tab to calculate descriptive statistics.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Dataset Selector Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span>Descriptive Statistics</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Compute column-level summary statistics (mean, std dev, median, IQR, CV) for all numeric variables.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Dataset Selector Dropdown */}
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400 font-medium">Dataset:</span>
            <select
              value={selectedDatasetId}
              onChange={(e) => {
                setSelectedDatasetId(e.target.value);
                setStatistics(null);
                setError(null);
              }}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500 max-w-xs"
            >
              {attached_datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name || ds.file_name} ({ds.row_count ?? "?"}r × {ds.column_count ?? "?"}c)
                </option>
              ))}
            </select>
          </div>

          <Button
            size="sm"
            onClick={handleCalculateStatistics}
            disabled={calculating || !selectedDatasetId}
          >
            <Calculator className="w-3.5 h-3.5 mr-1.5" />
            {calculating ? "Calculating..." : statistics ? "Recalculate Statistics" : "Calculate Statistics"}
          </Button>

          {selectedDatasetId && (
            <Link href={`/datasets/${selectedDatasetId}`} passHref>
              <Button variant="outline" size="sm">
                <ExternalLink className="w-3.5 h-3.5 mr-1" />
                Inspect Standalone
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Selected Dataset Summary Badge */}
      {selectedDataset && (
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center space-x-3">
            <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
            <div>
              <span className="font-semibold text-slate-100">{selectedDataset.name || selectedDataset.file_name}</span>
              <span className="text-slate-400 ml-2">({selectedDataset.file_name})</span>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-slate-400">
            <span>Rows: <strong className="text-slate-200">{selectedDataset.row_count ?? 0}</strong></span>
            <span>Columns: <strong className="text-slate-200">{selectedDataset.column_count ?? 0}</strong></span>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleCalculateStatistics}>
            Retry
          </Button>
        </div>
      )}

      {/* Provenance & Results */}
      {statistics ? (
        <div className="space-y-6">
          {/* Provenance Card */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex items-center space-x-2">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              <span>Experiment: <strong className="text-slate-200">{experiment.name}</strong></span>
              <span>•</span>
              <span>Dataset ID: <code className="text-cyan-300 font-mono">{statistics.dataset_id || selectedDatasetId}</code></span>
            </div>
            <div className="flex items-center space-x-3">
              <span>Engine: <strong className="text-slate-300">Module 3 Descriptive Statistics</strong></span>
              <span>•</span>
              <span>Software Version: <strong className="text-slate-300">SynDataX v1.0.0</strong></span>
            </div>
          </div>

          <DescriptiveStatisticsCard report={statistics} />
        </div>
      ) : !calculating && !error ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <Calculator className="w-10 h-10 text-cyan-500/50 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">Statistics Calculation Ready</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
            Click "Calculate Statistics" above to compute numerical summary statistics for the selected dataset.
          </p>
          <Button size="sm" onClick={handleCalculateStatistics}>
            <Calculator className="w-3.5 h-3.5 mr-1.5" />
            Calculate Statistics
          </Button>
        </Card>
      ) : null}
    </div>
  );
};
