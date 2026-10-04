"use client";

import React, { useState } from "react";
import { AlertTriangle, Calculator, CheckCircle2, ChevronRight, FlaskConical, Play } from "lucide-react";
import { Button } from "../ui/Button";
import { ColumnMetadata } from "../../lib/types/dataset";
import { Comparison, ComparisonCreateRequest, Experiment } from "../../lib/types/experiment";
import { runExperimentalComparison } from "../../lib/api/experiments";

interface ExperimentalComparisonPanelProps {
  experiment: Experiment;
  columns: (ColumnMetadata | string)[];
  onComparisonExecuted?: (comparison: Comparison) => void;
}

export const ExperimentalComparisonPanel: React.FC<ExperimentalComparisonPanelProps> = ({
  experiment,
  columns: rawColumns,
  onComparisonExecuted,
}) => {
  const columns = rawColumns.map((c) => (typeof c === "string" ? c : c.name));
  const [comparisonName, setComparisonName] = useState("Group Measurement Comparison");
  const [comparisonType, setComparisonType] = useState<"two_group" | "anova" | "nonparametric">("two_group");
  const [measurementColumn, setMeasurementColumn] = useState(columns[0] || "");
  const [groupColumn, setGroupColumn] = useState(columns.find((c) => c.toLowerCase().includes("group")) || columns[1] || "");
  const [selectedGroupA, setSelectedGroupA] = useState<string>(experiment.groups[0]?.id || "");
  const [selectedGroupB, setSelectedGroupB] = useState<string>(experiment.groups[1]?.id || "");
  const [method, setMethod] = useState("welch_ttest");
  const [alpha, setAlpha] = useState("0.05");
  const [paired, setPaired] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<Comparison | null>(
    experiment.comparisons && experiment.comparisons.length > 0 ? experiment.comparisons[0] : null
  );

  const handleRun = async () => {
    if (!measurementColumn) {
      setError("Please select a measurement column.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: ComparisonCreateRequest = {
        name: comparisonName,
        comparison_type: comparisonType,
        measurement_column: measurementColumn,
        group_column: groupColumn || undefined,
        group_a_id: selectedGroupA || undefined,
        group_b_id: selectedGroupB || undefined,
        method,
        alpha: parseFloat(alpha),
        paired,
      };

      const result = await runExperimentalComparison(experiment.id, request);
      setActiveResult(result);
      if (onComparisonExecuted) onComparisonExecuted(result);
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to execute experimental comparison.");
    } finally {
      setLoading(false);
    }
  };

  const statRes = activeResult?.result_summary?.statistical_result;
  const groupSummaries = activeResult?.result_summary?.group_summaries || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Module 6 — Experimental Group Comparison</h3>
            <p className="text-xs text-slate-400">
              Contextualize dataset observations within experimental groups and execute deterministic hypothesis tests.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Form Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950 border border-slate-800/80 p-4 rounded-xl">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Comparison Title</label>
          <input
            type="text"
            value={comparisonName}
            onChange={(e) => setComparisonName(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Comparison Framework</label>
          <select
            value={comparisonType}
            onChange={(e: any) => {
              setComparisonType(e.target.value);
              if (e.target.value === "anova") setMethod("one_way_anova");
              else if (e.target.value === "nonparametric") setMethod("mann_whitney");
              else setMethod("welch_ttest");
            }}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="two_group">Two-Group Comparison (Parametric)</option>
            <option value="anova">Multi-Group ANOVA</option>
            <option value="nonparametric">Non-Parametric Comparison</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Statistical Test Method</label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            {comparisonType === "two_group" && (
              <>
                <option value="welch_ttest">Welch's t-test (Default, Unequal Var)</option>
                <option value="student_ttest">Student's t-test (Equal Var)</option>
                <option value="paired_ttest">Paired t-test</option>
              </>
            )}
            {comparisonType === "anova" && (
              <>
                <option value="one_way_anova">One-Way ANOVA</option>
                <option value="welch_anova">Welch's ANOVA</option>
              </>
            )}
            {comparisonType === "nonparametric" && (
              <>
                <option value="mann_whitney">Mann-Whitney U Test (Independent)</option>
                <option value="wilcoxon_signed_rank">Wilcoxon Signed-Rank Test (Paired)</option>
                <option value="kruskal_wallis">Kruskal-Wallis H Test (Multi-Group)</option>
              </>
            )}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Measurement Column (Y)</label>
          <select
            value={measurementColumn}
            onChange={(e) => setMeasurementColumn(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            {columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Group Column (X)</label>
          <select
            value={groupColumn}
            onChange={(e) => setGroupColumn(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="">(None - Use Experiment Groups)</option>
            {columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">Significance Level (α)</label>
          <select
            value={alpha}
            onChange={(e) => setAlpha(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="0.05">α = 0.05 (Default)</option>
            <option value="0.01">α = 0.01 (Strict)</option>
            <option value="0.10">α = 0.10 (Exploratory)</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end">
        <Button variant="primary" size="md" onClick={handleRun} isLoading={loading}>
          <Play className="w-4 h-4 mr-2" /> Run Experimental Comparison
        </Button>
      </div>

      {/* Results Section */}
      {activeResult && statRes && (
        <div className="space-y-6 pt-4 border-t border-slate-800">
          {/* Transparent Scientific Factual Result Box */}
          <div className="p-4 bg-slate-950 border border-cyan-800/50 rounded-xl space-y-2">
            <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-xs">
              <Calculator className="w-4 h-4" />
              <span>Statistical Evidence Statement</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-mono bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              "{statRes.statement}"
            </p>
          </div>

          {/* Group Summaries Table */}
          {groupSummaries.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-200">Experimental Groups Observation Summary</h4>
              <div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-2.5">Group</th>
                      <th className="px-4 py-2.5">Total N</th>
                      <th className="px-4 py-2.5">Valid N</th>
                      <th className="px-4 py-2.5">Missing</th>
                      <th className="px-4 py-2.5">Mean</th>
                      <th className="px-4 py-2.5">Std Dev</th>
                      <th className="px-4 py-2.5">Median</th>
                      <th className="px-4 py-2.5">IQR</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/60">
                    {groupSummaries.map((g, idx) => {
                      const colStat = g.descriptive_stats?.statistics?.[0];
                      return (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          <td className="px-4 py-2 font-semibold text-slate-200">{g.group_name}</td>
                          <td className="px-4 py-2">{g.sample_size_total}</td>
                          <td className="px-4 py-2 text-emerald-400 font-medium">{g.sample_size_valid}</td>
                          <td className="px-4 py-2 text-amber-400">{g.missing_count}</td>
                          <td className="px-4 py-2 font-mono">{colStat?.mean !== null ? colStat?.mean?.toFixed(4) : "-"}</td>
                          <td className="px-4 py-2 font-mono">{colStat?.std !== null ? colStat?.std?.toFixed(4) : "-"}</td>
                          <td className="px-4 py-2 font-mono">{colStat?.median !== null ? colStat?.median?.toFixed(4) : "-"}</td>
                          <td className="px-4 py-2 font-mono">{colStat?.iqr !== null ? colStat?.iqr?.toFixed(4) : "-"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Test Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Statistic ({statRes.statistic_name})</span>
              <span className="text-sm font-bold font-mono text-slate-100">{statRes.statistic_value ?? "-"}</span>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">p-value</span>
              <span className={`text-sm font-bold font-mono ${statRes.is_significant ? "text-emerald-400" : "text-slate-200"}`}>
                {statRes.p_value ?? "-"}
              </span>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Effect Size</span>
              <span className="text-xs font-semibold text-cyan-400 block">{statRes.effect_size?.interpretation || "-"}</span>
              <span className="text-[10px] text-slate-400 font-mono">value = {statRes.effect_size?.value ?? "-"}</span>
            </div>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Decision (α={statRes.alpha})</span>
              <span className={`text-xs font-bold ${statRes.is_significant ? "text-emerald-400" : "text-amber-400"}`}>
                {statRes.is_significant ? "Statistically Significant" : "Not Significant"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
