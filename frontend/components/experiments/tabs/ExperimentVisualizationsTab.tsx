"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  ExternalLink,
  FileSpreadsheet,
  AlertCircle,
  Info,
  RefreshCw,
} from "lucide-react";
import { DatasetPreviewResponse, ColumnMetadata } from "../../../lib/types/dataset";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { getDatasetPreview } from "../../../lib/api/datasets";
import { VisualizationPanel } from "../../visualization/VisualizationPanel";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";

interface ExperimentVisualizationsTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentVisualizationsTab: React.FC<ExperimentVisualizationsTabProps> = ({
  workspace,
}) => {
  const { experiment, attached_datasets } = workspace;

  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [errorColumns, setErrorColumns] = useState<string | null>(null);

  // Sync selected dataset when attached datasets change
  useEffect(() => {
    if (attached_datasets.length > 0) {
      if (!selectedDatasetId || !attached_datasets.some((d) => d.id === selectedDatasetId)) {
        setSelectedDatasetId(attached_datasets[0].id);
      }
    } else {
      setSelectedDatasetId("");
      setColumns([]);
    }
  }, [attached_datasets]);

  // Fetch preview columns when selected dataset changes
  const loadColumns = async () => {
    if (!selectedDatasetId) return;

    setLoadingColumns(true);
    setErrorColumns(null);

    try {
      const preview = await getDatasetPreview(selectedDatasetId, 1);
      setColumns(preview.columns || []);
    } catch (err: any) {
      setErrorColumns(err.detail || "Failed to load column metadata for visualization.");
    } finally {
      setLoadingColumns(false);
    }
  };

  useEffect(() => {
    if (selectedDatasetId) {
      loadColumns();
    }
  }, [selectedDatasetId]);

  const selectedDataset = attached_datasets.find((d) => d.id === selectedDatasetId);

  if (attached_datasets.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <BarChart3 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Attached Datasets</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No datasets are attached to this experiment yet. Attach a dataset from the Datasets tab to generate scientific visualizations.
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
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span>Scientific Visualizations</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Generate interactive exploratory plots (Histograms, Box Plots, Scatter Plots, Bar Charts) server-side via Python.
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

      {/* Provenance Card */}
      {selectedDatasetId && (
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
          <div className="flex items-center space-x-2">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Experiment: <strong className="text-slate-200">{experiment.name}</strong></span>
            <span>•</span>
            <span>Dataset ID: <code className="text-cyan-300 font-mono">{selectedDatasetId}</code></span>
          </div>
          <div className="flex items-center space-x-3">
            <span>Engine: <strong className="text-slate-300">Module 4 Scientific Visualization</strong></span>
            <span>•</span>
            <span>Software Version: <strong className="text-slate-300">SynDataX v1.0.0</strong></span>
          </div>
        </div>
      )}

      {/* Columns Loading / Error / Content State */}
      {loadingColumns ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <div className="h-5 w-40 bg-slate-800 rounded animate-pulse mx-auto mb-2" />
          <p className="text-xs text-slate-400">Loading dataset variables for plot configuration...</p>
        </Card>
      ) : errorColumns ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorColumns}</span>
          </div>
          <Button variant="outline" size="sm" onClick={loadColumns}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry
          </Button>
        </div>
      ) : selectedDatasetId && columns.length > 0 ? (
        <VisualizationPanel key={selectedDatasetId} datasetId={selectedDatasetId} columns={columns} />
      ) : null}
    </div>
  );
};
