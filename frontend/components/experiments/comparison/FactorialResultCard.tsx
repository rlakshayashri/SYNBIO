"use client";

import React from "react";
import dynamic from "next/dynamic";
import {
  Calculator,
  AlertTriangle,
  Info,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  GitCommit,
  Layers,
  Sparkles,
  BarChart3,
  Split,
} from "lucide-react";
import { FactorialComparison, TwoWayAnovaResult, AnovaEffectResult } from "../../../lib/types/factorial";
import { Card } from "../../ui/Card";
import { Badge } from "../../ui/Badge";

// Dynamically import Plotly with SSR disabled for interaction profile
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface FactorialResultCardProps {
  comparison: FactorialComparison;
}

export const FactorialResultCard: React.FC<FactorialResultCardProps> = ({ comparison }) => {
  // Support both two_way_anova_result attribute and result_summary
  const result: TwoWayAnovaResult | undefined =
    comparison.two_way_anova_result || (comparison.result_summary as any)?.effects
      ? (comparison.result_summary as TwoWayAnovaResult)
      : undefined;

  if (!result || !result.effects) {
    return (
      <Card className="p-8 bg-slate-900/60 border-slate-800 text-center text-xs text-slate-400">
        <Info className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        No detailed Two-Way ANOVA results payload available for this comparison.
      </Card>
    );
  }

  const formatNumber = (val: number | null | undefined, precision: number = 4): string => {
    if (val === null || val === undefined || isNaN(val)) return "N/A";
    return Number(val.toFixed(precision)).toString();
  };

  const formatPValue = (p: number | null | undefined): string => {
    if (p === null || p === undefined || isNaN(p)) return "N/A";
    if (p < 0.0001) return "< 0.0001";
    return p.toFixed(4);
  };

  const getEffectInterpretationColor = (interp?: string | null) => {
    switch (interp?.toLowerCase()) {
      case "large":
        return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
      case "medium":
        return "text-cyan-400 border-cyan-500/30 bg-cyan-500/10";
      case "small":
        return "text-amber-400 border-amber-500/30 bg-amber-500/10";
      default:
        return "text-slate-400 border-slate-700 bg-slate-800/40";
    }
  };

  // Find effects
  const effectKeys = Object.keys(result.effects);
  const factorAKey = effectKeys.find((k) => k === result.factor_a_column) || result.factor_a_column;
  const factorBKey = effectKeys.find((k) => k === result.factor_b_column) || result.factor_b_column;
  const interactionKey =
    effectKeys.find((k) => k.includes("×") || k.includes(":") || k.includes(result.factor_a_column)) ||
    `${result.factor_a_column} × ${result.factor_b_column}`;

  const effectA: AnovaEffectResult | undefined = result.effects[factorAKey];
  const effectB: AnovaEffectResult | undefined = result.effects[factorBKey];
  const effectInt: AnovaEffectResult | undefined =
    result.effects[interactionKey] ||
    Object.values(result.effects).find(
      (e) => e.effect_name.includes("×") || (e.effect_name.includes(":") && e.effect_name !== "Residual")
    );
  const effectRes: AnovaEffectResult | undefined = result.effects["Residual"];

  const orderedEffects: AnovaEffectResult[] = [];
  if (effectA) orderedEffects.push(effectA);
  if (effectB) orderedEffects.push(effectB);
  if (effectInt) orderedEffects.push(effectInt);
  if (effectRes) orderedEffects.push(effectRes);

  // Remaining effects if any
  Object.values(result.effects).forEach((eff) => {
    if (!orderedEffects.some((oe) => oe.effect_name === eff.effect_name)) {
      orderedEffects.push(eff);
    }
  });

  // Cell Sample Sizes
  const cellEntries = Object.entries(result.cell_sample_sizes || {});

  return (
    <div className="space-y-6">
      {/* 1. Header & Evidence Statement Banner */}
      <div className="p-5 rounded-xl bg-slate-950 border border-cyan-500/40 shadow-xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold text-sm">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span>Two-Way Factorial ANOVA Evidence</span>
            <Badge variant="info" className="text-[10px] ml-2 text-cyan-300 border-cyan-500/40">
              {result.anova_type} SS
            </Badge>
            <Badge variant="neutral" className="text-[10px] text-slate-400 border-slate-700">
              {result.contrast_coding}
            </Badge>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400">Design:</span>
            <Badge variant={result.is_balanced ? "pass" : "neutral"} className="text-[10px]">
              {result.design_balance}
            </Badge>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400 font-mono text-[11px]">
              N = {result.valid_rows_used} valid rows ({result.total_rows_input} input)
            </span>
          </div>
        </div>

        {/* Scientific Statement */}
        <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
          <div className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Automated Scientific Inference</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-mono">
            "{result.scientific_statement}"
          </p>
        </div>

        {/* Epistemological Disclaimer */}
        <div className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/80 flex items-start space-x-2 text-[11px] text-slate-400">
          <Info className="w-4 h-4 text-cyan-400/80 flex-shrink-0 mt-0.5" />
          <p>
            Statistical significance indicates non-additive variation across factor levels; it does not independently establish causation or biological mechanism.
          </p>
        </div>
      </div>

      {/* 2. Key Effects Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        {/* Factor A Main Effect Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Factor A: {result.factor_a_column}
            </span>
            <Badge variant={effectA?.is_significant ? "pass" : "neutral"} className="text-[9px]">
              {effectA?.is_significant ? "Significant" : "NS"}
            </Badge>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold font-mono text-slate-100">
              F = {formatNumber(effectA?.f_statistic, 2)}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              (p = {formatPValue(effectA?.p_value)})
            </span>
          </div>
          {effectA?.partial_eta_squared !== undefined && (
            <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 flex justify-between">
              <span>Partial η²: <strong className="text-cyan-400 font-mono">{formatNumber(effectA.partial_eta_squared, 3)}</strong></span>
              {effectA.effect_size_interpretation && (
                <span className={`px-1.5 py-0.2 rounded border text-[9px] uppercase font-bold ${getEffectInterpretationColor(effectA.effect_size_interpretation)}`}>
                  {effectA.effect_size_interpretation}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Factor B Main Effect Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Factor B: {result.factor_b_column}
            </span>
            <Badge variant={effectB?.is_significant ? "pass" : "neutral"} className="text-[9px]">
              {effectB?.is_significant ? "Significant" : "NS"}
            </Badge>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold font-mono text-slate-100">
              F = {formatNumber(effectB?.f_statistic, 2)}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              (p = {formatPValue(effectB?.p_value)})
            </span>
          </div>
          {effectB?.partial_eta_squared !== undefined && (
            <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 flex justify-between">
              <span>Partial η²: <strong className="text-cyan-400 font-mono">{formatNumber(effectB.partial_eta_squared, 3)}</strong></span>
              {effectB.effect_size_interpretation && (
                <span className={`px-1.5 py-0.2 rounded border text-[9px] uppercase font-bold ${getEffectInterpretationColor(effectB.effect_size_interpretation)}`}>
                  {effectB.effect_size_interpretation}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Interaction Effect Card */}
        <div
          className={`p-4 rounded-xl border space-y-2 ${
            effectInt?.is_significant
              ? "bg-cyan-950/30 border-cyan-500/60 ring-1 ring-cyan-500/20"
              : "bg-slate-950/80 border-slate-800"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-1">
              <Split className="w-3.5 h-3.5 text-cyan-400" />
              <span>Interaction (A × B)</span>
            </span>
            <Badge variant={effectInt?.is_significant ? "pass" : "neutral"} className="text-[9px]">
              {effectInt?.is_significant ? "Significant Interaction" : "No Interaction"}
            </Badge>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold font-mono text-cyan-300">
              F = {formatNumber(effectInt?.f_statistic, 2)}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              (p = {formatPValue(effectInt?.p_value)})
            </span>
          </div>
          {effectInt?.partial_eta_squared !== undefined && (
            <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80 flex justify-between">
              <span>Partial η²: <strong className="text-cyan-300 font-mono">{formatNumber(effectInt.partial_eta_squared, 3)}</strong></span>
              {effectInt.effect_size_interpretation && (
                <span className={`px-1.5 py-0.2 rounded border text-[9px] uppercase font-bold ${getEffectInterpretationColor(effectInt.effect_size_interpretation)}`}>
                  {effectInt.effect_size_interpretation}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 3. Primary Two-Way ANOVA Table */}
      <Card className="p-5 bg-slate-900/60 border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2 text-slate-200 font-bold text-xs">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Two-Way ANOVA Table (Type III Sums of Squares)</span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Model: {result.model_formula}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-semibold">
                <th className="py-2.5 px-3">Source of Variation</th>
                <th className="py-2.5 px-3 text-right">SS</th>
                <th className="py-2.5 px-3 text-right">df</th>
                <th className="py-2.5 px-3 text-right">MS</th>
                <th className="py-2.5 px-3 text-right">F-statistic</th>
                <th className="py-2.5 px-3 text-right">p-value</th>
                <th className="py-2.5 px-3 text-center">Decision</th>
                <th className="py-2.5 px-3 text-right">Partial η²</th>
                <th className="py-2.5 px-3 text-right">95% CI</th>
                <th className="py-2.5 px-3 text-center">Effect Size</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-200">
              {orderedEffects.map((eff) => {
                const isInteraction =
                  eff.effect_name.includes("×") ||
                  (eff.effect_name.includes(":") && eff.effect_name !== "Residual");
                const isResidual = eff.effect_name === "Residual";

                return (
                  <tr
                    key={eff.effect_name}
                    className={`hover:bg-slate-800/30 transition-colors ${
                      isInteraction ? "bg-cyan-950/20 font-semibold" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3 font-sans text-slate-100 flex items-center space-x-1.5">
                      {isInteraction && <Split className="w-3.5 h-3.5 text-cyan-400" />}
                      <span>{eff.effect_name}</span>
                    </td>
                    <td className="py-2.5 px-3 text-right">{formatNumber(eff.sum_of_squares, 3)}</td>
                    <td className="py-2.5 px-3 text-right">{eff.degrees_of_freedom}</td>
                    <td className="py-2.5 px-3 text-right">{formatNumber(eff.mean_square, 3)}</td>
                    <td className="py-2.5 px-3 text-right">
                      {eff.f_statistic !== null && eff.f_statistic !== undefined
                        ? formatNumber(eff.f_statistic, 3)
                        : "—"}
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right ${
                        eff.is_significant ? "text-emerald-400 font-bold" : "text-slate-300"
                      }`}
                    >
                      {eff.p_value !== null && eff.p_value !== undefined ? formatPValue(eff.p_value) : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-center font-sans">
                      {isResidual ? (
                        <span className="text-slate-600">—</span>
                      ) : eff.is_significant ? (
                        <Badge variant="pass" className="text-[9px]">
                          p &lt; α
                        </Badge>
                      ) : (
                        <Badge variant="neutral" className="text-[9px]">
                          NS
                        </Badge>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right text-cyan-400">
                      {eff.partial_eta_squared !== null && eff.partial_eta_squared !== undefined
                        ? formatNumber(eff.partial_eta_squared, 4)
                        : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right text-[11px] text-slate-400">
                      {eff.partial_eta_squared_ci
                        ? `[${formatNumber(eff.partial_eta_squared_ci[0], 2)}, ${formatNumber(
                            eff.partial_eta_squared_ci[1],
                            2
                          )}]`
                        : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-center font-sans">
                      {eff.effect_size_interpretation ? (
                        <span
                          className={`px-1.5 py-0.5 rounded border text-[9px] uppercase font-bold ${getEffectInterpretationColor(
                            eff.effect_size_interpretation
                          )}`}
                        >
                          {eff.effect_size_interpretation}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 4. Cell Design & Observations Summary */}
      <Card className="p-5 bg-slate-900/60 border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <span className="text-xs font-bold text-slate-300 flex items-center space-x-2">
            <GitCommit className="w-3.5 h-3.5 text-cyan-400" />
            <span>Factorial Design Matrix Sample Sizes</span>
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            {result.factor_a_levels.length} × {result.factor_b_levels.length} Factorial Cells
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 text-xs">
          {cellEntries.map(([cellName, count]) => (
            <div key={cellName} className="p-2 rounded-lg bg-slate-950 border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block truncate" title={cellName}>
                {cellName}
              </span>
              <span className="text-xs font-bold font-mono text-cyan-400">n = {count}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* 5. Simple Main Effects Breakdown (when interaction is significant) */}
      {result.interaction_significant && result.simple_effects && result.simple_effects.length > 0 && (
        <Card className="p-5 bg-slate-900/60 border-cyan-500/40 shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h4 className="text-xs font-bold text-cyan-400 flex items-center space-x-2">
                <Split className="w-4 h-4" />
                <span>Simple Main Effects Decomposition</span>
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Because Factor A × Factor B is significant, main effects are decomposed into slice-specific simple effects.
              </p>
            </div>
            <Badge variant="pass" className="text-[9px]">
              Interaction Detected
            </Badge>
          </div>

          <div className="space-y-4">
            {result.simple_effects.map((se, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-slate-200">
                    Effect of <span className="text-cyan-400 font-mono">{se.factor_name}</span> at{" "}
                    <span className="text-slate-400 font-mono">
                      {se.at_factor_name} = "{se.at_level}"
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 font-mono text-xs">
                    <span>F = {formatNumber(se.f_statistic, 3)}</span>
                    <span className={se.is_significant ? "text-emerald-400 font-bold" : "text-slate-400"}>
                      p = {formatPValue(se.p_value)}
                    </span>
                    <Badge variant={se.is_significant ? "pass" : "neutral"} className="text-[9px]">
                      {se.is_significant ? "Significant" : "NS"}
                    </Badge>
                  </div>
                </div>

                {/* Pairwise post-hoc if present in slice */}
                {se.pairwise_comparisons && se.pairwise_comparisons.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                      Pairwise Comparisons ({result.post_hoc_method.toUpperCase()} adjusted)
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                      {se.pairwise_comparisons.map((pc, pcIdx) => (
                        <div key={pcIdx} className="p-2 rounded bg-slate-900/60 border border-slate-800 flex justify-between items-center">
                          <span className="text-slate-300">{pc.group1} vs {pc.group2}</span>
                          <span className={pc.is_significant ? "text-emerald-400 font-bold" : "text-slate-400"}>
                            p_adj = {formatPValue(pc.p_adjusted ?? pc.p_raw)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 6. Marginal Post-Hoc Comparisons (when interaction is non-significant) */}
      {!result.interaction_significant && result.post_hoc_comparisons && result.post_hoc_comparisons.length > 0 && (
        <Card className="p-5 bg-slate-900/60 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                <span>Marginal Post-Hoc Comparisons ({result.post_hoc_method.toUpperCase()})</span>
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Interaction is not significant; marginal comparisons evaluate main effect differences across levels.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-semibold font-sans">
                  <th className="py-2 px-3">Contrast</th>
                  <th className="py-2 px-3 text-right">Statistic</th>
                  <th className="py-2 px-3 text-right">p (raw)</th>
                  <th className="py-2 px-3 text-right">p (adjusted)</th>
                  <th className="py-2 px-3 text-center">Adjustment</th>
                  <th className="py-2 px-3 text-center">Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {result.post_hoc_comparisons.map((ph, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-sans text-slate-100">
                      {ph.group1} vs {ph.group2}
                    </td>
                    <td className="py-2 px-3 text-right">{formatNumber(ph.statistic, 3)}</td>
                    <td className="py-2 px-3 text-right">{formatPValue(ph.p_raw)}</td>
                    <td className={`py-2 px-3 text-right ${ph.is_significant ? "text-emerald-400 font-bold" : ""}`}>
                      {formatPValue(ph.p_adjusted)}
                    </td>
                    <td className="py-2 px-3 text-center font-sans text-slate-400 uppercase text-[10px]">
                      {ph.correction_method}
                    </td>
                    <td className="py-2 px-3 text-center font-sans">
                      {ph.is_significant ? (
                        <Badge variant="pass" className="text-[9px]">
                          p &lt; α
                        </Badge>
                      ) : (
                        <Badge variant="neutral" className="text-[9px]">
                          NS
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 7. Assumption Checks & Data Accounting */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Assumption Diagnostics */}
        <Card className="p-4 bg-slate-900/60 border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-slate-200 font-bold text-xs border-b border-slate-800 pb-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>Model Assumption Diagnostics</span>
          </div>

          <div className="space-y-2">
            {Object.entries(result.assumptions || {}).map(([key, asmp]) => (
              <div key={key} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">{asmp.name}</span>
                  {asmp.passed ? (
                    <Badge variant="pass" className="text-[9px] flex items-center space-x-1">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      <span>Passed</span>
                    </Badge>
                  ) : (
                    <Badge variant="error" className="text-[9px] flex items-center space-x-1">
                      <XCircle className="w-2.5 h-2.5" />
                      <span>Violated</span>
                    </Badge>
                  )}
                </div>
                <p className="text-[11px] text-slate-400">{asmp.details}</p>
                {asmp.p_value !== null && asmp.p_value !== undefined && (
                  <span className="text-[10px] text-slate-500 font-mono block">
                    Stat = {formatNumber(asmp.statistic, 3)}, p = {formatPValue(asmp.p_value)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* Data Accounting & Exclusions */}
        <Card className="p-4 bg-slate-900/60 border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-slate-200 font-bold text-xs border-b border-slate-800 pb-2">
            <Info className="w-4 h-4 text-cyan-400" />
            <span>Missing Data & Observation Accounting</span>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Total Observations Ingested:</span>
              <span className="font-mono font-bold text-slate-200">{result.total_rows_input}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Valid Observations Analyzed:</span>
              <span className="font-mono font-bold text-emerald-400">{result.valid_rows_used}</span>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Excluded / Dropped Rows:</span>
              <span className={`font-mono font-bold ${result.excluded_rows_count > 0 ? "text-amber-400" : "text-slate-400"}`}>
                {result.excluded_rows_count}
              </span>
            </div>

            {/* Warnings list if any */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] space-y-1">
                <div className="font-semibold flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Validation Warnings</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                  {result.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
