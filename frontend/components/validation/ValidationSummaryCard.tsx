import React from "react";
import { ShieldCheck, AlertTriangle, XCircle, FileWarning, Layers, Activity, Columns } from "lucide-react";
import { ValidationResult, ValidationStatus } from "../../lib/types/validation";
import { Badge } from "../ui/Badge";
import { Alert } from "../ui/Alert";

interface ValidationSummaryCardProps {
  validation: ValidationResult;
}

export const ValidationSummaryCard: React.FC<ValidationSummaryCardProps> = ({ validation }) => {
  const getStatusBadge = (status: ValidationStatus) => {
    switch (status) {
      case "PASS":
        return (
          <Badge variant="pass" className="px-3 py-1 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            PASS
          </Badge>
        );
      case "WARNING":
        return (
          <Badge variant="warning" className="px-3 py-1 text-xs">
            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
            WARNING
          </Badge>
        );
      case "ERROR":
        return (
          <Badge variant="error" className="px-3 py-1 text-xs">
            <XCircle className="w-3.5 h-3.5 mr-1" />
            ERROR
          </Badge>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h3 className="text-base font-bold text-slate-100">DATA QUALITY REPORT</h3>
            {getStatusBadge(validation.overall_status)}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Scientific data validation summary evaluated across {validation.row_count} rows and {validation.column_count} columns.
          </p>
        </div>
      </div>

      {/* Summary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <FileWarning className="w-4 h-4 text-amber-400" />
            <span>Missing Values</span>
          </div>
          <p className="text-xl font-bold text-slate-100">
            {validation.summary.missing_values}
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Duplicate Rows</span>
          </div>
          <p className="text-xl font-bold text-slate-100">
            {validation.summary.duplicate_rows}
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Activity className="w-4 h-4 text-rose-400" />
            <span>Potential Outliers</span>
          </div>
          <p className="text-xl font-bold text-slate-100">
            {validation.summary.potential_outliers}
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Columns className="w-4 h-4 text-purple-400" />
            <span>Empty Columns</span>
          </div>
          <p className="text-xl font-bold text-slate-100">
            {validation.summary.empty_columns}
          </p>
        </div>
      </div>

      {/* Warnings List */}
      {validation.warnings.length > 0 && (
        <Alert
          type={validation.overall_status === "ERROR" ? "error" : "warning"}
          title="Statistical Anomaly Warnings"
        >
          <ul className="list-disc list-inside space-y-1 text-xs mt-1">
            {validation.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}
    </div>
  );
};
