import React from "react";
import { Calculator, Binary, FileText, Info } from "lucide-react";
import { DescriptiveStatisticsResult } from "../../lib/types/statistics";
import { Badge } from "../ui/Badge";

interface DescriptiveStatisticsCardProps {
  report: DescriptiveStatisticsResult;
}

export const DescriptiveStatisticsCard: React.FC<DescriptiveStatisticsCardProps> = ({ report }) => {
  const formatStat = (val: number | null, precision: number = 4): string => {
    if (val === null || val === undefined) return "N/A";
    return Number(val.toFixed(precision)).toString();
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h3 className="text-base font-bold text-slate-100">DESCRIPTIVE STATISTICS REPORT</h3>
            <Badge variant="info">Module 3</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Numerical summary calculations computed across {report.numeric_column_count} numeric variables and {report.row_count} rows.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span>Rows</span>
          </div>
          <p className="text-xl font-bold text-slate-100">{report.row_count.toLocaleString()}</p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Binary className="w-4 h-4 text-emerald-400" />
            <span>Numeric Variables</span>
          </div>
          <p className="text-xl font-bold text-slate-100">{report.numeric_column_count}</p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <FileText className="w-4 h-4 text-amber-400" />
            <span>Non-Numeric Variables</span>
          </div>
          <p className="text-xl font-bold text-slate-100">{report.non_numeric_column_count}</p>
        </div>
      </div>

      {/* Scientific Statistics Table */}
      {report.statistics.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-sans">
              <tr>
                <th className="py-2.5 px-3 font-semibold sticky left-0 bg-slate-950 min-w-[130px]">Variable</th>
                <th className="py-2.5 px-3 font-semibold text-center">N</th>
                <th className="py-2.5 px-3 font-semibold text-center">Missing</th>
                <th className="py-2.5 px-3 font-semibold text-right">Mean</th>
                <th className="py-2.5 px-3 font-semibold text-right">Std Dev</th>
                <th className="py-2.5 px-3 font-semibold text-right">Min</th>
                <th className="py-2.5 px-3 font-semibold text-right">Q1 (25%)</th>
                <th className="py-2.5 px-3 font-semibold text-right">Median</th>
                <th className="py-2.5 px-3 font-semibold text-right">Q3 (75%)</th>
                <th className="py-2.5 px-3 font-semibold text-right">Max</th>
                <th className="py-2.5 px-3 font-semibold text-right">IQR</th>
                <th className="py-2.5 px-3 font-semibold text-right">Range</th>
                <th className="py-2.5 px-3 font-semibold text-right">CV</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {report.statistics.map((stat) => (
                <tr key={stat.column} className="hover:bg-slate-800/30 odd:bg-slate-900/50 even:bg-slate-950/20">
                  <td className="py-2 px-3 font-sans font-medium text-slate-100 sticky left-0 bg-slate-900 border-r border-slate-800/60 truncate">
                    {stat.column}
                  </td>
                  <td className="py-2 px-3 text-center text-slate-300">{stat.count}</td>
                  <td className="py-2 px-3 text-center text-amber-400/90">
                    {stat.missing_count > 0 ? stat.missing_count : 0}
                  </td>
                  <td className="py-2 px-3 text-right text-cyan-300 font-semibold">{formatStat(stat.mean)}</td>
                  <td className="py-2 px-3 text-right">{formatStat(stat.std)}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{formatStat(stat.min)}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{formatStat(stat.q1)}</td>
                  <td className="py-2 px-3 text-right text-emerald-300 font-semibold">{formatStat(stat.median)}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{formatStat(stat.q3)}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{formatStat(stat.max)}</td>
                  <td className="py-2 px-3 text-right">{formatStat(stat.iqr)}</td>
                  <td className="py-2 px-3 text-right">{formatStat(stat.range)}</td>
                  <td className="py-2 px-3 text-right text-amber-300">
                    {stat.cv !== null ? formatStat(stat.cv) : <span className="text-slate-600 italic font-sans text-[11px]">N/A</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-slate-950/40 border border-slate-800/60 p-4 rounded-lg text-center text-xs text-slate-400">
          No numeric variables available in this dataset to compute descriptive statistics.
        </div>
      )}

      {/* Skipped Non-Numeric Variables Section */}
      {report.skipped_columns.length > 0 && (
        <div className="bg-slate-950/40 border border-slate-800/60 p-4 rounded-lg text-xs space-y-2">
          <div className="flex items-center space-x-2 text-slate-300 font-medium">
            <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>Non-numeric variables (Skipped for numerical statistics):</span>
          </div>
          <div className="flex flex-wrap gap-1.5 pl-6">
            {report.skipped_columns.map((col) => (
              <Badge key={col} variant="neutral">
                {col}
              </Badge>
            ))}
          </div>
          <p className="text-[11px] text-slate-400 pl-6 italic">
            Descriptive numerical statistics were calculated only for numeric variables.
          </p>
        </div>
      )}
    </div>
  );
};
