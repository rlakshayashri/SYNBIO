import React from "react";
import { Table, Eye, AlertCircle } from "lucide-react";
import { DatasetPreviewResponse } from "../../lib/types/dataset";
import { Badge } from "../ui/Badge";

interface DataPreviewTableProps {
  preview: DatasetPreviewResponse | null;
  isLoading: boolean;
  error: string | null;
}

export const DataPreviewTable: React.FC<DataPreviewTableProps> = ({
  preview,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
        <div className="inline-flex items-center justify-center p-3 rounded-full bg-slate-800 text-cyan-400 mb-3 animate-pulse">
          <Eye className="w-6 h-6" />
        </div>
        <p className="text-xs text-slate-300 font-medium">Loading dataset preview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center space-x-2 text-rose-400 text-sm font-semibold mb-2">
          <AlertCircle className="w-4 h-4" />
          <span>Unable to load preview</span>
        </div>
        <p className="text-xs text-slate-400">{error}</p>
      </div>
    );
  }

  if (!preview || preview.data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-xs">
        No preview rows available for this dataset.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Table className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-slate-100">Dataset Preview</h3>
          <Badge variant="neutral">Top {preview.preview_rows} Rows</Badge>
        </div>
        <span className="text-xs text-slate-400">
          Showing {preview.preview_rows} of {preview.row_count} total rows
        </span>
      </div>

      {/* Responsive Horizontal Scroll Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left border-collapse min-w-full">
          <thead>
            <tr className="bg-slate-950 border-b border-slate-800">
              <th className="py-2.5 px-3 text-[11px] font-semibold text-slate-400 border-r border-slate-800/60 w-12 text-center">
                #
              </th>
              {preview.columns.map((col) => (
                <th
                  key={col.name}
                  className="py-2.5 px-3 text-xs font-semibold text-slate-200 border-r border-slate-800/60 whitespace-nowrap min-w-[140px]"
                >
                  <div className="flex items-center justify-between space-x-2">
                    <span className="truncate">{col.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      {col.dtype}
                    </span>
                  </div>
                  {col.null_count > 0 && (
                    <div className="text-[10px] text-amber-400/90 mt-0.5 font-normal">
                      {col.null_count} null ({col.null_percentage}%)
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
            {preview.data.map((row, idx) => (
              <tr
                key={idx}
                className="hover:bg-slate-800/40 transition-colors odd:bg-slate-900/50 even:bg-slate-950/20"
              >
                <td className="py-2 px-3 text-[11px] text-slate-500 border-r border-slate-800/60 text-center select-none font-sans">
                  {idx + 1}
                </td>
                {preview.columns.map((col) => {
                  const val = row[col.name];
                  const isNull = val === null || val === undefined;
                  return (
                    <td
                      key={col.name}
                      className="py-2 px-3 border-r border-slate-800/60 text-slate-200 whitespace-nowrap max-w-[240px] truncate"
                    >
                      {isNull ? (
                        <span className="text-slate-600 italic font-sans text-[11px]">null</span>
                      ) : (
                        String(val)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
