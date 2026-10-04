"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Play,
  AlertCircle,
  ExternalLink,
  FileSpreadsheet,
  Layers,
  Info,
} from "lucide-react";
import { Dataset } from "../../../lib/types/dataset";
import { ValidationResult } from "../../../lib/types/validation";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { validateDataset } from "../../../lib/api/validation";
import { ValidationSummaryCard } from "../../validation/ValidationSummaryCard";
import { ValidationDetailsTabs } from "../../validation/ValidationDetailsTabs";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";

interface ExperimentValidationTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentValidationTab: React.FC<ExperimentValidationTabProps> = ({ workspace }) => {
  const { experiment, attached_datasets } = workspace;

  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync selected dataset when attached datasets change
  useEffect(() => {
    if (attached_datasets.length > 0) {
      if (!selectedDatasetId || !attached_datasets.some((d) => d.id === selectedDatasetId)) {
        setSelectedDatasetId(attached_datasets[0].id);
        setValidation(null);
      }
    } else {
      setSelectedDatasetId("");
      setValidation(null);
    }
  }, [attached_datasets]);

  const selectedDataset = attached_datasets.find((d) => d.id === selectedDatasetId);

  const handleRunValidation = async () => {
    if (!selectedDatasetId) return;

    setValidating(true);
    setError(null);

    try {
      const result = await validateDataset(selectedDatasetId);
      setValidation(result);
    } catch (err: any) {
      setError(err.detail || "Data validation execution failed. Please try again.");
    } finally {
      setValidating(false);
    }
  };

  if (attached_datasets.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <ShieldCheck className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Attached Datasets</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No datasets are attached to this experiment yet. Attach a raw dataset from the Datasets tab to begin data quality validation.
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
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>Data Validation & Quality Checks</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluate missingness, duplicate rows, detected data types, empty columns, and IQR outliers on experiment datasets.
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
                setValidation(null);
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
            onClick={handleRunValidation}
            disabled={validating || !selectedDatasetId}
          >
            <Play className="w-3.5 h-3.5 mr-1.5" />
            {validating ? "Running Validation..." : validation ? "Re-run Validation" : "Run Validation"}
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
          <Button variant="outline" size="sm" onClick={handleRunValidation}>
            Retry
          </Button>
        </div>
      )}

      {/* Provenance & Results */}
      {validation ? (
        <div className="space-y-6">
          {/* Provenance Card */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex items-center space-x-2">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              <span>Experiment: <strong className="text-slate-200">{experiment.name}</strong></span>
              <span>•</span>
              <span>Dataset ID: <code className="text-cyan-300 font-mono">{validation.dataset_id || selectedDatasetId}</code></span>
            </div>
            <div className="flex items-center space-x-3">
              <span>Engine: <strong className="text-slate-300">Module 2 Scientific Validator</strong></span>
              <span>•</span>
              <span>Software Version: <strong className="text-slate-300">SynDataX v1.0.0</strong></span>
            </div>
          </div>

          <ValidationSummaryCard validation={validation} />
          <ValidationDetailsTabs validation={validation} />
        </div>
      ) : !validating && !error ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <ShieldCheck className="w-10 h-10 text-cyan-500/50 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">Validation Ready</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
            Click "Run Validation" above to execute data quality checks on the selected dataset.
          </p>
          <Button size="sm" onClick={handleRunValidation}>
            <Play className="w-3.5 h-3.5 mr-1.5" />
            Run Validation
          </Button>
        </Card>
      ) : null}
    </div>
  );
};
