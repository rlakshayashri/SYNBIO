import React from "react";
import { FileText, Rows, Columns, HardDrive, Calendar, Tag } from "lucide-react";
import { Dataset } from "../../lib/types/dataset";
import { Badge } from "../ui/Badge";

interface DatasetMetadataCardProps {
  dataset: Dataset;
}

export const DatasetMetadataCard: React.FC<DatasetMetadataCardProps> = ({ dataset }) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-100">{dataset.name}</h2>
            <Badge variant="info">{dataset.file_type.toUpperCase()}</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-slate-500" />
            <span>Filename: {dataset.file_name}</span>
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5 text-cyan-400" />
          <span>Uploaded: {new Date(dataset.created_at).toLocaleString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Rows className="w-4 h-4 text-cyan-400" />
            <span>Rows</span>
          </div>
          <p className="text-lg font-bold text-slate-100">
            {dataset.row_count !== null ? dataset.row_count.toLocaleString() : "N/A"}
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Columns className="w-4 h-4 text-cyan-400" />
            <span>Columns</span>
          </div>
          <p className="text-lg font-bold text-slate-100">
            {dataset.column_count !== null ? dataset.column_count.toLocaleString() : "N/A"}
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <HardDrive className="w-4 h-4 text-cyan-400" />
            <span>File Size</span>
          </div>
          <p className="text-lg font-bold text-slate-100">{formatFileSize(dataset.file_size)}</p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span>Format</span>
          </div>
          <p className="text-lg font-bold text-slate-100">{dataset.file_type.toUpperCase()}</p>
        </div>
      </div>
    </div>
  );
};
