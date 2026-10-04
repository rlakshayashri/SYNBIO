"use client";

import React from "react";
import {
  Calculator,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Layers,
  Scale,
} from "lucide-react";
import { Comparison } from "../../../lib/types/experiment";
import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";

interface StatisticalResultCardProps {
  comparison: Comparison;
}

export const StatisticalResultCard: React.FC<StatisticalResultCardProps> = ({ comparison }) => {
  const resultSummary = comparison.result_summary || {};
  const statRes = resultSummary.statistical_result;
  const groupSummaries = resultSummary.group_summaries || [];

  if (!statRes) {
    return (
      <Card className="p-6 bg-slate-900/60 border-slate-800 text-center text-xs text-slate-400">
        No detailed statistical result payload available for this comparison.
      </Card>
    );
  }

  const formatNumber = (val: number | null | undefined, precision: number = 4): string => {
    if (val === null || val === undefined) return "N/A";
    return Number(val.toFixed(precision)).toString();
  };

  return (
    <div className="space-y-6">
      {/* Evidence Statement Banner */}
      <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/40 shadow-lg space-y-2">
        <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-xs">
          <Calculator className="w-4 h-4" />
          <span>Statistical Evidence Statement</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed font-mono bg-slate-900/90 p-3 rounded-lg border border-slate-800">
          "{statRes.statement}"
        </p>
      </div>

      {/* Main Test Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
            Test Statistic ({statRes.statistic_name})
          </span>
          <span className="text-base font-bold font-mono text-slate-100">
            {formatNumber(statRes.statistic_value)}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
            p-value
          </span>
          <span
            className={`text-base font-bold font-mono ${
              statRes.is_significant ? "text-emerald-400" : "text-slate-200"
            }`}
          >
            {formatNumber(statRes.p_value)}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
            Effect Size
          </span>
          <span className="text-xs font-bold text-cyan-400 block truncate">
            {statRes.effect_size?.name || "Effect Size"}: {formatNumber(statRes.effect_size?.value)}
          </span>
          {statRes.effect_size?.interpretation && (
            <span className="text-[10px] text-slate-400 block capitalize mt-0.5">
              ({statRes.effect_size.interpretation})
            </span>
          )}
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
            Decision (α = {statRes.alpha})
          </span>
          <span
            className={`text-xs font-bold block ${
              statRes.is_significant ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {statRes.is_significant ? "Statistically Significant" : "Not Significant"}
          </span>
        </div>
      </div>

      {/* Confidence Interval & Degrees of Freedom */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {statRes.confidence_interval && (
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-300 font-medium">
              <Scale className="w-4 h-4 text-cyan-400" />
              <span>
                {(statRes.confidence_interval.level * 100).toFixed(0)}% Confidence Interval (
                {statRes.confidence_interval.metric || "Difference"}):
              </span>
            </div>
            <span className="font-mono text-cyan-300 font-semibold">
              [{formatNumber(statRes.confidence_interval.lower)}, {formatNumber(statRes.confidence_interval.upper)}]
            </span>
          </div>
        )}

        {statRes.df !== undefined && statRes.df !== null && (
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-300 font-medium">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>Degrees of Freedom (df):</span>
            </div>
            <span className="font-mono text-purple-300 font-semibold">
              {typeof statRes.df === "object" ? JSON.stringify(statRes.df) : statRes.df}
            </span>
          </div>
        )}
      </div>

      {/* Experimental Groups Summary Table */}
      {groupSummaries.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>Group Observation Summaries</span>
          </h4>
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 font-sans border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Group</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Total N</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Valid N</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Missing</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Mean</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Std Dev</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Median</th>
                  <th className="py-2.5 px-3 font-semibold text-right">IQR</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {groupSummaries.map((g: any, idx: number) => {
                  const colStat = g.descriptive_stats?.statistics?.[0];
                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 odd:bg-slate-900/50 even:bg-slate-950/20">
                      <td className="py-2 px-3 font-sans font-medium text-slate-100 flex items-center space-x-2">
                        <span>{g.group_name}</span>
                        {g.is_control && <Badge variant="pass">Control</Badge>}
                      </td>
                      <td className="py-2 px-3 text-center text-slate-300">{g.sample_size_total}</td>
                      <td className="py-2 px-3 text-center text-emerald-400 font-medium">{g.sample_size_valid}</td>
                      <td className="py-2 px-3 text-center text-amber-400">{g.missing_count}</td>
                      <td className="py-2 px-3 text-right text-cyan-300 font-semibold">{formatNumber(colStat?.mean)}</td>
                      <td className="py-2 px-3 text-right">{formatNumber(colStat?.std)}</td>
                      <td className="py-2 px-3 text-right text-emerald-300 font-semibold">{formatNumber(colStat?.median)}</td>
                      <td className="py-2 px-3 text-right">{formatNumber(colStat?.iqr)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Assumption Checks */}
      {statRes.assumptions && statRes.assumptions.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-2">
            <Info className="w-4 h-4 text-cyan-400" />
            <span>Statistical Assumption Checks</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {statRes.assumptions.map((asm: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start space-x-3 text-xs"
              >
                {asm.passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-slate-200">{asm.name}</span>
                    <span
                      className={`text-[10px] font-bold ${
                        asm.passed ? "text-emerald-400" : "text-amber-400"
                      }`}
                    >
                      {asm.passed ? "PASSED" : "VIOLATED"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">{asm.details}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Post-Hoc Pairwise Comparisons Table */}
      {statRes.post_hoc && statRes.post_hoc.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-200">Post-Hoc Pairwise Comparisons</h4>
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 font-sans border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Group 1</th>
                  <th className="py-2.5 px-3 font-semibold">Group 2</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Statistic</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Raw p</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Adjusted p</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Significant</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {statRes.post_hoc.map((ph: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-sans font-medium text-slate-100">{ph.group1}</td>
                    <td className="py-2 px-3 font-sans font-medium text-slate-100">{ph.group2}</td>
                    <td className="py-2 px-3 text-right">{formatNumber(ph.statistic)}</td>
                    <td className="py-2 px-3 text-right text-slate-400">{formatNumber(ph.p_raw)}</td>
                    <td className="py-2 px-3 text-right text-cyan-300 font-semibold">{formatNumber(ph.p_adjusted)}</td>
                    <td className="py-2 px-3 text-center">
                      {ph.is_significant ? (
                        <span className="text-emerald-400 font-bold text-[10px]">YES</span>
                      ) : (
                        <span className="text-slate-500 text-[10px]">NO</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Warnings */}
      {statRes.warnings && statRes.warnings.length > 0 && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
          <div className="flex items-center space-x-2 font-semibold">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Statistical Execution Warnings</span>
          </div>
          <ul className="list-disc list-inside text-[11px] space-y-0.5 pl-2">
            {statRes.warnings.map((w: string, idx: number) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Provenance Card */}
      <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
        <div className="flex items-center space-x-2">
          <Info className="w-3.5 h-3.5 text-cyan-400" />
          <span>Comparison ID: <code className="text-cyan-300 font-mono">{comparison.id}</code></span>
          {comparison.analysis_id && (
            <>
              <span>•</span>
              <span>Analysis Record ID: <code className="text-slate-300 font-mono">{comparison.analysis_id}</code></span>
            </>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <span>Framework: <strong className="text-slate-300">{comparison.comparison_type}</strong></span>
          <span>•</span>
          <span>Engine: <strong className="text-slate-300">Module 5 Statistical Analysis</strong></span>
        </div>
      </div>
    </div>
  );
};
