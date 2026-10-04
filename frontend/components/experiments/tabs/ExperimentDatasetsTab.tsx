"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Database,
  Plus,
  Upload,
  Trash2,
  ExternalLink,
  FileSpreadsheet,
  AlertCircle,
  Link as LinkIcon,
} from "lucide-react";
import { Dataset } from "../../../lib/types/dataset";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { attachDataset, detachDataset, uploadAndAttachDataset } from "../../../lib/api/experiments";
import { getDatasets } from "../../../lib/api/datasets";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";

interface ExperimentDatasetsTabProps {
  workspace: ExperimentWorkspaceResponse;
  onRefreshWorkspace: () => void;
}

export const ExperimentDatasetsTab: React.FC<ExperimentDatasetsTabProps> = ({
  workspace,
  onRefreshWorkspace,
}) => {
  const { experiment, attached_datasets } = workspace;

  // Modals state
  const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Attach existing dataset state
  const [projectDatasets, setProjectDatasets] = useState<Dataset[]>([]);
  const [loadingProjectDatasets, setLoadingProjectDatasets] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [attaching, setAttaching] = useState(false);
  const [attachError, setAttachError] = useState<string | null>(null);

  // Upload new dataset state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Detach state
  const [detachingId, setDetachingId] = useState<string | null>(null);
  const [detachError, setDetachError] = useState<string | null>(null);

  const handleOpenAttachModal = async () => {
    setIsAttachModalOpen(true);
    setAttachError(null);
    setSelectedDatasetId("");
    setLoadingProjectDatasets(true);

    try {
      const allDatasets = await getDatasets(experiment.project_id);
      // Filter out datasets that are already attached to this experiment
      const attachedIds = new Set(attached_datasets.map((d) => d.id));
      const unattached = allDatasets.filter((d) => !attachedIds.has(d.id));
      setProjectDatasets(unattached);
      if (unattached.length > 0) {
        setSelectedDatasetId(unattached[0].id);
      }
    } catch (err: any) {
      setAttachError(err.detail || "Failed to load project datasets.");
    } finally {
      setLoadingProjectDatasets(false);
    }
  };

  const handleAttachDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDatasetId) {
      setAttachError("Please select a dataset to attach.");
      return;
    }

    setAttaching(true);
    setAttachError(null);

    try {
      await attachDataset(experiment.id, selectedDatasetId);
      setIsAttachModalOpen(false);
      onRefreshWorkspace();
    } catch (err: any) {
      setAttachError(err.detail || "Failed to attach dataset.");
    } finally {
      setAttaching(false);
    }
  };

  const handleUploadDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      await uploadAndAttachDataset(experiment.id, uploadFile, uploadName.trim() || undefined);
      setUploadFile(null);
      setUploadName("");
      setIsUploadModalOpen(false);
      onRefreshWorkspace();
    } catch (err: any) {
      setUploadError(err.detail || "Failed to upload and attach dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleDetachDataset = async (datasetId: string) => {
    if (!confirm("Are you sure you want to detach this dataset from the experiment?")) {
      return;
    }

    setDetachingId(datasetId);
    setDetachError(null);

    try {
      await detachDataset(experiment.id, datasetId);
      onRefreshWorkspace();
    } catch (err: any) {
      setDetachError(err.detail || "Failed to detach dataset.");
    } finally {
      setDetachingId(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>Experiment Datasets</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Attach raw experimental datasets or upload new tabular data files directly to this experiment.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={handleOpenAttachModal}>
            <LinkIcon className="w-3.5 h-3.5 mr-1.5" />
            Attach Existing
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setIsUploadModalOpen(true);
              setUploadError(null);
              setUploadFile(null);
              setUploadName("");
            }}
          >
            <Upload className="w-3.5 h-3.5 mr-1.5" />
            Upload New File
          </Button>
        </div>
      </div>

      {detachError && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{detachError}</span>
        </div>
      )}

      {/* Attach Existing Modal */}
      {isAttachModalOpen && (
        <Card className="p-5 bg-slate-900 border-cyan-500/40 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-sm font-bold text-cyan-400 flex items-center space-x-2">
              <LinkIcon className="w-4 h-4" />
              <span>Attach Existing Project Dataset</span>
            </h4>
            <button
              onClick={() => setIsAttachModalOpen(false)}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Cancel
            </button>
          </div>

          {attachError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{attachError}</span>
            </div>
          )}

          {loadingProjectDatasets ? (
            <div className="text-xs text-slate-400 py-4 text-center">
              Loading available project datasets...
            </div>
          ) : projectDatasets.length === 0 ? (
            <div className="text-xs text-slate-400 py-4 text-center space-y-2">
              <p>No unattached datasets available in this project.</p>
              <p className="text-slate-500">
                All project datasets are already attached, or no datasets exist yet in project.
              </p>
            </div>
          ) : (
            <form onSubmit={handleAttachDataset} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">
                  Select Unattached Dataset *
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                >
                  {projectDatasets.map((ds) => (
                    <option key={ds.id} value={ds.id}>
                      {ds.name || ds.file_name} ({ds.row_count ?? "?"} rows × {ds.column_count ?? "?"} cols)
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsAttachModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={attaching || !selectedDatasetId}>
                  {attaching ? "Attaching..." : "Attach Dataset"}
                </Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Upload New File Modal */}
      {isUploadModalOpen && (
        <Card className="p-5 bg-slate-900 border-cyan-500/40 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-sm font-bold text-cyan-400 flex items-center space-x-2">
              <Upload className="w-4 h-4" />
              <span>Upload & Attach Dataset</span>
            </h4>
            <button
              onClick={() => setIsUploadModalOpen(false)}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Cancel
            </button>
          </div>

          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <form onSubmit={handleUploadDataset} className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-300 mb-1">
                Data File (CSV, TSV, XLSX) *
              </label>
              <input
                type="file"
                accept=".csv,.tsv,.txt,.xlsx,.xls"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setUploadFile(e.target.files[0]);
                  }
                }}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs file:mr-4 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-cyan-950 file:text-cyan-400 hover:file:bg-cyan-900"
                required
              />
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1">
                Dataset Name (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Plate Reader Run 2026-10-04"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsUploadModalOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={uploading || !uploadFile}>
                {uploading ? "Uploading..." : "Upload & Attach"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Datasets List */}
      {attached_datasets.length === 0 ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <FileSpreadsheet className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">No Datasets Attached</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Attach an existing dataset or upload a new experimental raw data file to enable statistical analysis and quality validation.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {attached_datasets.map((dataset) => (
            <Card
              key={dataset.id}
              className="p-4 bg-slate-900/60 border-slate-800 hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex items-start space-x-3">
                <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 mt-0.5">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>

                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-bold text-slate-100">{dataset.name || dataset.file_name}</h4>
                    <span className="text-xs text-slate-400 font-mono">({dataset.file_name})</span>
                  </div>

                  <div className="flex items-center space-x-4 text-xs text-slate-400">
                    <span>
                      <strong className="text-slate-200">{dataset.row_count ?? 0}</strong> rows
                    </span>
                    <span>•</span>
                    <span>
                      <strong className="text-slate-200">{dataset.column_count ?? 0}</strong> columns
                    </span>
                    <span>•</span>
                    <span>{formatFileSize(dataset.file_size)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 self-end sm:self-center">
                <Link href={`/datasets/${dataset.id}`} passHref>
                  <Button variant="outline" size="sm">
                    <ExternalLink className="w-3.5 h-3.5 mr-1" />
                    Inspect Standalone
                  </Button>
                </Link>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDetachDataset(dataset.id)}
                  disabled={detachingId === dataset.id}
                  className="text-rose-400 hover:text-rose-300 hover:border-rose-500/40"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1" />
                  {detachingId === dataset.id ? "Detaching..." : "Detach"}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
