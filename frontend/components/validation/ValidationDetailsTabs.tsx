import React, { useState } from "react";
import { ValidationResult } from "../../lib/types/validation";
import { Badge } from "../ui/Badge";

interface ValidationDetailsTabsProps {
  validation: ValidationResult;
}

export const ValidationDetailsTabs: React.FC<ValidationDetailsTabsProps> = ({ validation }) => {
  const [activeTab, setActiveTab] = useState<"missing" | "duplicates" | "dtypes" | "outliers" | "empty">("missing");

  const tabs = [
    { id: "missing", label: "Missing Values", count: validation.checks.missing_values.length },
    { id: "duplicates", label: "Duplicate Rows", count: validation.checks.duplicates.duplicate_count },
    { id: "dtypes", label: "Data Types", count: validation.checks.data_types.length },
    { id: "outliers", label: "Potential Outliers", count: validation.checks.outliers.length },
    { id: "empty", label: "Empty Columns", count: validation.checks.empty_columns.length },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
      <h4 className="text-sm font-semibold text-slate-200 mb-4">Validation Check Details</h4>

      {/* Tabs Header */}
      <div className="flex border-b border-slate-800 space-x-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap flex items-center space-x-2 ${
              activeTab === tab.id
                ? "border-cyan-500 text-cyan-400 bg-cyan-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <span>{tab.label}</span>
            {tab.count > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {/* Missing Values Tab */}
        {activeTab === "missing" && (
          <div>
            {validation.checks.missing_values.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">✓ Zero missing values detected across all columns.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2.5 px-4 font-semibold">Column</th>
                      <th className="py-2.5 px-4 font-semibold">Missing Count</th>
                      <th className="py-2.5 px-4 font-semibold">Missing Percentage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                    {validation.checks.missing_values.map((item) => (
                      <tr key={item.column} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 font-sans font-medium">{item.column}</td>
                        <td className="py-2.5 px-4 text-amber-400">{item.missing_count}</td>
                        <td className="py-2.5 px-4">{item.missing_percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Duplicate Rows Tab */}
        {activeTab === "duplicates" && (
          <div>
            {validation.checks.duplicates.duplicate_count === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">✓ Zero exact duplicate rows detected.</p>
            ) : (
              <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">Exact Duplicate Rows Count:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {validation.checks.duplicates.duplicate_count}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">Duplicate Percentage:</span>
                  <span className="font-mono font-bold text-slate-200">
                    {validation.checks.duplicates.duplicate_percentage}%
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Data Types Tab */}
        {activeTab === "dtypes" && (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Column Name</th>
                  <th className="py-2.5 px-4 font-semibold">Detected Data Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                {validation.checks.data_types.map((item) => (
                  <tr key={item.column} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-4 font-sans font-medium">{item.column}</td>
                    <td className="py-2.5 px-4">
                      <Badge variant="info">{item.detected_dtype}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Outliers Tab */}
        {activeTab === "outliers" && (
          <div>
            <p className="text-[11px] text-slate-400 mb-3 italic">
              Statistical flags calculated using $Q1 - 1.5 \times \text{"{"}IQR\text{"}"}$ and $Q3 + 1.5 \times \text{"{"}IQR\text{"}"}$. Flagged values represent potential scientific anomalies and should not be automatically deleted.
            </p>
            {validation.checks.outliers.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">✓ Zero statistical IQR outliers detected in numeric columns.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2.5 px-4 font-semibold">Numeric Column</th>
                      <th className="py-2.5 px-4 font-semibold">Outlier Count</th>
                      <th className="py-2.5 px-4 font-semibold">Outlier %</th>
                      <th className="py-2.5 px-4 font-semibold">Lower Bound</th>
                      <th className="py-2.5 px-4 font-semibold">Upper Bound</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                    {validation.checks.outliers.map((item) => (
                      <tr key={item.column} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-4 font-sans font-medium">{item.column}</td>
                        <td className="py-2.5 px-4 text-rose-400">{item.outlier_count}</td>
                        <td className="py-2.5 px-4">{item.outlier_percentage}%</td>
                        <td className="py-2.5 px-4 text-slate-400">{item.lower_bound}</td>
                        <td className="py-2.5 px-4 text-slate-400">{item.upper_bound}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Empty Columns Tab */}
        {activeTab === "empty" && (
          <div>
            {validation.checks.empty_columns.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">✓ Zero completely empty columns detected.</p>
            ) : (
              <div className="bg-rose-950/20 border border-rose-800/50 p-4 rounded-lg">
                <p className="text-xs font-semibold text-rose-300 mb-2">
                  The following columns contain 100% missing values:
                </p>
                <div className="flex flex-wrap gap-2">
                  {validation.checks.empty_columns.map((col) => (
                    <Badge key={col} variant="error">
                      {col}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
