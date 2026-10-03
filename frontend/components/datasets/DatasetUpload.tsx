import React, { useState, useRef } from "react";
import { UploadCloud, FileSpreadsheet, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "../ui/Button";
import { uploadDataset } from "../../lib/api/datasets";
import { Dataset } from "../../lib/types/dataset";

interface DatasetUploadProps {
  projectId: string;
  onUploadSuccess: (dataset: Dataset) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({
  projectId,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [customName, setCustomName] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) return;

    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "csv" && ext !== "xlsx" && ext !== "xls") {
      setError("Unsupported file format. Please select a .csv or .xlsx file.");
      setFile(null);
      return;
    }

    setError(null);
    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const dataset = await uploadDataset(projectId, file, customName.trim() || undefined);
      setFile(null);
      setCustomName("");
      onUploadSuccess(dataset);
    } catch (err: any) {
      setError(
        err.detail || "Unable to upload dataset. Please check that the file is a valid CSV or XLSX file."
      );
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} bytes`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      <h3 className="text-base font-semibold text-slate-100 mb-1 flex items-center gap-2">
        <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
        Ingest Scientific Dataset
      </h3>
      <p className="text-xs text-slate-400 mb-5">
        Upload tabular scientific data files (.csv, .xlsx) for validation and analysis.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-rose-950/40 border border-rose-800/50 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-cyan-500 bg-cyan-950/20"
            : file
            ? "border-emerald-500/50 bg-emerald-950/10"
            : "border-slate-800 hover:border-slate-700 bg-slate-950/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
          className="hidden"
        />

        {file ? (
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-3 rounded-lg max-w-md mx-auto">
            <div className="flex items-center space-x-3 text-left overflow-hidden">
              <div className="p-2 rounded bg-emerald-500/10 text-emerald-400">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-slate-200 truncate">{file.name}</p>
                <p className="text-[11px] text-slate-400">{formatFileSize(file.size)}</p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
              className="text-slate-400 hover:text-slate-200 text-xs font-medium px-2 py-1"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-12 h-12 rounded-full bg-slate-800/80 text-cyan-400 flex items-center justify-center mx-auto mb-1">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-xs font-medium text-slate-200">
              Drag & drop dataset file or <span className="text-cyan-400">browse</span>
            </p>
            <p className="text-[11px] text-slate-500">Supports CSV (.csv) and Excel (.xlsx) up to 50 MB</p>
          </div>
        )}
      </div>

      {file && (
        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Dataset Display Name (Optional)
            </label>
            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder={file.name}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-600 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          <div className="flex justify-end">
            <Button
              variant="primary"
              size="md"
              onClick={handleUpload}
              isLoading={isUploading}
            >
              Upload & Process Dataset
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
