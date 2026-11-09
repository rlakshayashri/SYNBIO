"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  FlaskConical,
  Plus,
  Play,
  AlertCircle,
  Users,
  Database,
  History,
  Layers,
  Split,
  Trash2,
} from "lucide-react";
import { ColumnMetadata } from "../../../lib/types/dataset";
import {
  Comparison,
  ComparisonCreateRequest,
  ExperimentWorkspaceResponse,
} from "../../../lib/types/experiment";
import {
  ExperimentalFactor,
  FactorialComparison,
  FactorialComparisonCreate,
} from "../../../lib/types/factorial";
import {
  runExperimentalComparison,
  getFactorialComparisons,
  runFactorialComparison,
  deleteFactorialComparison,
  getExperimentalFactors,
} from "../../../lib/api/experiments";
import { getDatasetPreview } from "../../../lib/api/datasets";
import { StatisticalResultCard } from "../comparison/StatisticalResultCard";
import { FactorialResultCard } from "../comparison/FactorialResultCard";
import { FactorManagementPanel } from "../comparison/FactorManagementPanel";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";

interface ExperimentComparisonsTabProps {
  workspace: ExperimentWorkspaceResponse;
  onRefreshWorkspace?: () => void;
}

export const ExperimentComparisonsTab: React.FC<ExperimentComparisonsTabProps> = ({
  workspace,
  onRefreshWorkspace = () => {},
}) => {
  const { experiment, attached_datasets, groups, comparisons } = workspace;

  // Sub-tab Navigation
  const [activeSubTab, setActiveSubTab] = useState<"factorial" | "group_comparisons" | "factors">("factorial");

  // --- Factorial Analysis (Module 9) State ---
  const [factorialComparisons, setFactorialComparisons] = useState<FactorialComparison[]>([]);
  const [selectedFactorialId, setSelectedFactorialId] = useState<string | null>(null);
  const [loadingFactorialList, setLoadingFactorialList] = useState(false);
  const [factors, setFactors] = useState<ExperimentalFactor[]>([]);

  const [isFactorialModalOpen, setIsFactorialModalOpen] = useState(false);
  const [factorialTitle, setFactorialTitle] = useState("Two-Factor Factorial Analysis");
  const [factorialDatasetId, setFactorialDatasetId] = useState<string>(attached_datasets[0]?.id || "");
  const [factorialFactorAId, setFactorialFactorAId] = useState<string>("");
  const [factorialFactorBId, setFactorialFactorBId] = useState<string>("");
  const [factorialFactorACol, setFactorialFactorACol] = useState<string>("");
  const [factorialFactorBCol, setFactorialFactorBCol] = useState<string>("");
  const [factorialMeasurementCol, setFactorialMeasurementCol] = useState<string>("");
  const [factorialAlpha, setFactorialAlpha] = useState<string>("0.05");
  const [factorialPostHoc, setFactorialPostHoc] = useState<string>("tukey");
  const [factorialCheckAssumptions, setFactorialCheckAssumptions] = useState<boolean>(true);

  const [executingFactorial, setExecutingFactorial] = useState(false);
  const [factorialError, setFactorialError] = useState<string | null>(null);
  const [factorialColumns, setFactorialColumns] = useState<ColumnMetadata[]>([]);
  const [loadingFactorialCols, setLoadingFactorialCols] = useState(false);

  // --- One-Factor Comparison State (Preserved) ---
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedComparisonId, setSelectedComparisonId] = useState<string | null>(
    comparisons && comparisons.length > 0 ? comparisons[0].id : null
  );
  const [comparisonName, setComparisonName] = useState("Group Comparison Analysis");
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(attached_datasets[0]?.id || "");
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [comparisonType, setComparisonType] = useState<"two_group" | "anova" | "nonparametric">("two_group");
  const [selectedGroupA, setSelectedGroupA] = useState<string>(groups[0]?.id || "");
  const [selectedGroupB, setSelectedGroupB] = useState<string>(groups[1]?.id || "");
  const [groupColumn, setGroupColumn] = useState<string>("");
  const [measurementColumn, setMeasurementColumn] = useState<string>("");
  const [method, setMethod] = useState<string>("welch_ttest");
  const [alpha, setAlpha] = useState<string>("0.05");
  const [postHocMethod, setPostHocMethod] = useState<string>("none");
  const [paired, setPaired] = useState<boolean>(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load factors for this experiment
  const loadFactors = useCallback(async () => {
    try {
      const data = await getExperimentalFactors(experiment.id);
      setFactors(data);
    } catch {
      // Non-fatal
    }
  }, [experiment.id]);

  // Load factorial comparisons for this experiment
  const loadFactorialComparisons = useCallback(async () => {
    setLoadingFactorialList(true);
    try {
      const data = await getFactorialComparisons(experiment.id);
      setFactorialComparisons(data);
      if (data.length > 0 && !selectedFactorialId) {
        setSelectedFactorialId(data[0].id);
      }
    } catch {
      // Non-fatal
    } finally {
      setLoadingFactorialList(false);
    }
  }, [experiment.id, selectedFactorialId]);

  useEffect(() => {
    loadFactors();
    loadFactorialComparisons();
  }, [loadFactors, loadFactorialComparisons]);

  // Sync columns for one-factor comparisons
  useEffect(() => {
    if (attached_datasets.length > 0 && !selectedDatasetId) {
      setSelectedDatasetId(attached_datasets[0].id);
    }
  }, [attached_datasets, selectedDatasetId]);

  useEffect(() => {
    const loadCols = async () => {
      if (!selectedDatasetId) return;
      setLoadingColumns(true);
      try {
        const preview = await getDatasetPreview(selectedDatasetId, 1);
        const cols = preview.columns || [];
        setColumns(cols);

        const numeric = cols.filter((c) => c.dtype.includes("int") || c.dtype.includes("float"));
        if (numeric.length > 0 && !measurementColumn) {
          setMeasurementColumn(numeric[0].name);
        }
        if (cols.length > 0 && !groupColumn) {
          const gCol = cols.find((c) => c.name.toLowerCase().includes("group")) || cols[0];
          setGroupColumn(gCol.name);
        }
      } catch {
        // Ignore preview error
      } finally {
        setLoadingColumns(false);
      }
    };
    loadCols();
  }, [selectedDatasetId]);

  // Sync columns for factorial comparison
  useEffect(() => {
    if (attached_datasets.length > 0 && !factorialDatasetId) {
      setFactorialDatasetId(attached_datasets[0].id);
    }
  }, [attached_datasets, factorialDatasetId]);

  useEffect(() => {
    const loadFactCols = async () => {
      if (!factorialDatasetId) return;
      setLoadingFactorialCols(true);
      try {
        const preview = await getDatasetPreview(factorialDatasetId, 1);
        const cols = preview.columns || [];
        setFactorialColumns(cols);

        const numeric = cols.filter((c) => c.dtype.includes("int") || c.dtype.includes("float"));
        const categorical = cols.filter((c) => !c.dtype.includes("float"));

        if (numeric.length > 0) {
          setFactorialMeasurementCol(numeric[0].name);
        }
        if (categorical.length >= 2) {
          setFactorialFactorACol(categorical[0].name);
          setFactorialFactorBCol(categorical[1].name);
        } else if (cols.length >= 3) {
          setFactorialFactorACol(cols[0].name);
          setFactorialFactorBCol(cols[1].name);
        }
      } catch {
        // Ignore preview error
      } finally {
        setLoadingFactorialCols(false);
      }
    };
    loadFactCols();
  }, [factorialDatasetId]);

  // Handle execution of One-Factor comparison
  const handleRunComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!measurementColumn) {
      setError("Please select a measurement column.");
      return;
    }
    setExecuting(true);
    setError(null);
    try {
      const requestPayload: ComparisonCreateRequest = {
        name: comparisonName.trim() || "Group Comparison Analysis",
        comparison_type: comparisonType,
        group_a_id: selectedGroupA || undefined,
        group_b_id: selectedGroupB || undefined,
        measurement_column: measurementColumn,
        group_column: groupColumn || undefined,
        method: method as any,
        alpha: parseFloat(alpha),
        post_hoc_method: postHocMethod as any,
        paired,
      };
      const newComp = await runExperimentalComparison(experiment.id, requestPayload);
      setIsCreateModalOpen(false);
      onRefreshWorkspace();
      setSelectedComparisonId(newComp.id);
    } catch (err: any) {
      setError(err.detail || "Failed to execute experimental comparison. Please verify parameters.");
    } finally {
      setExecuting(false);
    }
  };

  // Handle execution of Two-Way Factorial Analysis
  const handleRunFactorialComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    setFactorialError(null);

    if (!factorialFactorACol || !factorialFactorBCol || !factorialMeasurementCol) {
      setFactorialError("Please select Factor A, Factor B, and Measurement columns.");
      return;
    }

    if (factorialFactorACol === factorialFactorBCol) {
      setFactorialError("Factor A and Factor B must be distinct dataset columns.");
      return;
    }

    if (
      factorialMeasurementCol === factorialFactorACol ||
      factorialMeasurementCol === factorialFactorBCol
    ) {
      setFactorialError("Measurement column cannot be identical to Factor A or Factor B.");
      return;
    }

    if (factorialFactorAId && factorialFactorBId && factorialFactorAId === factorialFactorBId) {
      setFactorialError("Factor A and Factor B cannot reference the identical conceptual factor.");
      return;
    }

    setExecutingFactorial(true);
    try {
      const payload: FactorialComparisonCreate = {
        name: factorialTitle.trim() || "Two-Factor Factorial Analysis",
        dataset_id: factorialDatasetId,
        factor_a_id: factorialFactorAId || undefined,
        factor_b_id: factorialFactorBId || undefined,
        factor_a_column: factorialFactorACol,
        factor_b_column: factorialFactorBCol,
        measurement_column: factorialMeasurementCol,
        alpha: parseFloat(factorialAlpha),
        post_hoc_method: factorialPostHoc,
        check_assumptions: factorialCheckAssumptions,
      };

      const created = await runFactorialComparison(experiment.id, payload);
      setIsFactorialModalOpen(false);
      onRefreshWorkspace();
      await loadFactorialComparisons();
      setSelectedFactorialId(created.id);
    } catch (err: any) {
      setFactorialError(err.detail || "Failed to execute factorial analysis. Please verify inputs and cell observations.");
    } finally {
      setExecutingFactorial(false);
    }
  };

  const handleDeleteFactorial = async (comparisonId: string) => {
    try {
      await deleteFactorialComparison(experiment.id, comparisonId);
      await loadFactorialComparisons();
      if (selectedFactorialId === comparisonId) {
        setSelectedFactorialId(null);
      }
    } catch (err: any) {
      setFactorialError(err.detail || "Failed to delete factorial comparison.");
    }
  };

  const selectedComparison = comparisons.find((c) => c.id === selectedComparisonId) || comparisons[0];
  const selectedFactorial = factorialComparisons.find((fc) => fc.id === selectedFactorialId) || factorialComparisons[0];

  const factorialNumericCols = factorialColumns.filter(
    (c) => c.dtype.includes("int") || c.dtype.includes("float")
  );

  if (attached_datasets.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <Database className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Attached Datasets</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No datasets are attached to this experiment yet. Attach a dataset from the Datasets tab to create factorial analyses.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Workflow Sub-Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <FlaskConical className="w-4 h-4 text-cyan-400" />
            <span>Experimental Comparisons & Factorial Analysis</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Two-way factorial ANOVA with interaction decomposition, assumption diagnostics, and multi-factor experimental modeling.
          </p>
        </div>

        {/* Sub-tab Pills */}
        <div className="flex items-center space-x-1 p-1 bg-slate-900 border border-slate-800 rounded-lg">
          <button
            type="button"
            onClick={() => setActiveSubTab("factorial")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
              activeSubTab === "factorial"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Split className="w-3.5 h-3.5" />
            <span>Two-Way Factorial ({factorialComparisons.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("group_comparisons")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
              activeSubTab === "group_comparisons"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>One-Factor ({comparisons.length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("factors")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
              activeSubTab === "factors"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Factors ({factors.length})</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 1. TWO-WAY FACTORIAL ANALYSIS VIEW (MODULE 9 PRIMARY)                    */}
      {/* ========================================================================= */}
      {activeSubTab === "factorial" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-400">
              Factorial ANOVA decomposes variation into <span className="text-slate-200 font-semibold">Factor A</span>,{" "}
              <span className="text-slate-200 font-semibold">Factor B</span>, and their{" "}
              <span className="text-cyan-400 font-semibold">Interaction (A × B)</span> using Type III sums of squares.
            </div>
            <Button
              size="sm"
              onClick={() => {
                setIsFactorialModalOpen(true);
                setFactorialError(null);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Run Factorial Analysis
            </Button>
          </div>

          {/* Factorial Analysis Execution Modal */}
          {isFactorialModalOpen && (
            <Card className="p-5 bg-slate-900 border-cyan-500/40 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h4 className="text-sm font-bold text-cyan-400 flex items-center space-x-2">
                  <Split className="w-4 h-4" />
                  <span>Configure Two-Way Factorial Analysis (ANOVA)</span>
                </h4>
                <button
                  onClick={() => setIsFactorialModalOpen(false)}
                  className="text-xs text-slate-500 hover:text-slate-300"
                >
                  Cancel
                </button>
              </div>

              {factorialError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{factorialError}</span>
                </div>
              )}

              <form onSubmit={handleRunFactorialComparison} className="space-y-4 text-xs">
                {/* Title & Dataset */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Analysis Title *</label>
                    <input
                      type="text"
                      value={factorialTitle}
                      onChange={(e) => setFactorialTitle(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Attached Dataset *</label>
                    <select
                      value={factorialDatasetId}
                      onChange={(e) => setFactorialDatasetId(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      required
                    >
                      {attached_datasets.map((ds) => (
                        <option key={ds.id} value={ds.id}>
                          {ds.name || ds.file_name} ({ds.row_count ?? "?"}r × {ds.column_count ?? "?"}c)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Factor A: Conceptual Factor & Dataset Column */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
                  <span className="text-xs font-bold text-cyan-400 block">Factor A Specification</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block font-medium text-slate-400 mb-1">
                        Conceptual Factor (Optional Definition)
                      </label>
                      <select
                        value={factorialFactorAId}
                        onChange={(e) => setFactorialFactorAId(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      >
                        <option value="">(None / Column Only)</option>
                        {factors.map((f) => (
                          <option key={f.id} value={f.id}>
                            {f.name} ({f.levels?.length || 0} levels)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block font-medium text-slate-300 mb-1">
                        Factor A Dataset Column *
                      </label>
                      <select
                        value={factorialFactorACol}
                        onChange={(e) => setFactorialFactorACol(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                        required
                      >
                        <option value="">Select Factor A column...</option>
                        {factorialColumns.map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name} ({c.dtype})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Factor B: Conceptual Factor & Dataset Column */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
                  <span className="text-xs font-bold text-cyan-400 block">Factor B Specification</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block font-medium text-slate-400 mb-1">
                        Conceptual Factor (Optional Definition)
                      </label>
                      <select
                        value={factorialFactorBId}
                        onChange={(e) => setFactorialFactorBId(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      >
                        <option value="">(None / Column Only)</option>
                        {factors.map((f) => (
                          <option key={f.id} value={f.id}>
                            {f.name} ({f.levels?.length || 0} levels)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block font-medium text-slate-300 mb-1">
                        Factor B Dataset Column *
                      </label>
                      <select
                        value={factorialFactorBCol}
                        onChange={(e) => setFactorialFactorBCol(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                        required
                      >
                        <option value="">Select Factor B column...</option>
                        {factorialColumns.map((c) => (
                          <option key={c.name} value={c.name}>
                            {c.name} ({c.dtype})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Measurement Column & Analysis Options */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">
                      Measurement Column (Y) *
                    </label>
                    <select
                      value={factorialMeasurementCol}
                      onChange={(e) => setFactorialMeasurementCol(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-cyan-400"
                      required
                    >
                      <option value="">Select response variable...</option>
                      {factorialNumericCols.map((c) => (
                        <option key={c.name} value={c.name}>
                          {c.name} ({c.dtype})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Significance Level (α)</label>
                    <select
                      value={factorialAlpha}
                      onChange={(e) => setFactorialAlpha(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="0.05">α = 0.05 (Default)</option>
                      <option value="0.01">α = 0.01 (Strict)</option>
                      <option value="0.10">α = 0.10 (Exploratory)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Post-Hoc Adjustment</label>
                    <select
                      value={factorialPostHoc}
                      onChange={(e) => setFactorialPostHoc(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="tukey">Tukey HSD</option>
                      <option value="bonferroni">Bonferroni</option>
                      <option value="holm">Holm</option>
                      <option value="none">None (Unadjusted)</option>
                    </select>
                  </div>
                </div>

                {/* Checkbox: Assumption checks */}
                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id="factAssumptionsCheck"
                    checked={factorialCheckAssumptions}
                    onChange={(e) => setFactorialCheckAssumptions(e.target.checked)}
                    className="rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-0"
                  />
                  <label htmlFor="factAssumptionsCheck" className="text-slate-300 font-medium cursor-pointer">
                    Compute Assumption Diagnostics (Residual Normality, Cell Homogeneity & Cook's Influence)
                  </label>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setIsFactorialModalOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" disabled={executingFactorial}>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    {executingFactorial ? "Executing Two-Way ANOVA..." : "Execute Factorial Analysis"}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Factorial History Cards */}
          {factorialComparisons.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-300 flex items-center space-x-2">
                  <History className="w-4 h-4 text-cyan-400" />
                  <span>Factorial Analysis Records ({factorialComparisons.length})</span>
                </h4>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {factorialComparisons.map((fcomp) => {
                  const isSelected = selectedFactorial?.id === fcomp.id;
                  const res = fcomp.two_way_anova_result || (fcomp.result_summary as any);
                  const isIntSig = res?.interaction_significant;

                  return (
                    <div
                      key={fcomp.id}
                      onClick={() => setSelectedFactorialId(fcomp.id)}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer relative group ${
                        isSelected
                          ? "bg-cyan-950/40 border-cyan-500/80 ring-1 ring-cyan-500/30 shadow-md"
                          : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-bold text-xs text-slate-100 flex items-center space-x-1.5">
                            <Split className="w-3 h-3 text-cyan-400" />
                            <span>{fcomp.name}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono mt-1">
                            {fcomp.factor_a_column} × {fcomp.factor_b_column} → {fcomp.measurement_column}
                          </div>
                        </div>

                        <div className="flex items-center space-x-1">
                          {isIntSig ? (
                            <Badge variant="pass" className="text-[9px] px-1.5 py-0.5">
                              Interaction Sig
                            </Badge>
                          ) : (
                            <Badge variant="neutral" className="text-[9px] px-1.5 py-0.5">
                              Main Effects
                            </Badge>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteFactorial(fcomp.id);
                            }}
                            className="text-slate-500 hover:text-rose-400 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete factorial comparison"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Active Factorial Result Card View */}
          {selectedFactorial ? (
            <FactorialResultCard comparison={selectedFactorial} />
          ) : (
            <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
              <Split className="w-10 h-10 text-cyan-500/50 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-slate-300">No Factorial Analyses Run Yet</h4>
              <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
                Execute a Two-Way ANOVA to test main effects, interaction effects, and simple main effect decompositions.
              </p>
              <Button
                size="sm"
                onClick={() => {
                  setIsFactorialModalOpen(true);
                  setFactorialError(null);
                }}
              >
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Run Factorial Analysis
              </Button>
            </Card>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. ONE-FACTOR GROUP COMPARISONS (ORIGINAL MODULE 6 WORKFLOW)              */}
      {/* ========================================================================= */}
      {activeSubTab === "group_comparisons" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-400">
              Contextualize experimental groups and execute statistical hypothesis tests (t-tests, one-way ANOVA, Mann-Whitney, Kruskal-Wallis).
            </div>
            <Button
              size="sm"
              onClick={() => {
                setIsCreateModalOpen(true);
                setError(null);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Run One-Factor Comparison
            </Button>
          </div>

          {/* New One-Factor Comparison Modal */}
          {isCreateModalOpen && (
            <Card className="p-5 bg-slate-900 border-cyan-500/40 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h4 className="text-sm font-bold text-cyan-400 flex items-center space-x-2">
                  <FlaskConical className="w-4 h-4" />
                  <span>Configure Experimental Group Comparison</span>
                </h4>
                <button
                  onClick={() => setIsCreateModalOpen(false)}
                  className="text-xs text-slate-500 hover:text-slate-300"
                >
                  Cancel
                </button>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleRunComparison} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Comparison Title *</label>
                    <input
                      type="text"
                      value={comparisonName}
                      onChange={(e) => setComparisonName(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Attached Dataset *</label>
                    <select
                      value={selectedDatasetId}
                      onChange={(e) => setSelectedDatasetId(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      required
                    >
                      {attached_datasets.map((ds) => (
                        <option key={ds.id} value={ds.id}>
                          {ds.name || ds.file_name} ({ds.row_count ?? "?"}r × {ds.column_count ?? "?"}c)
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Group A (Control / Baseline)</label>
                    <select
                      value={selectedGroupA}
                      onChange={(e) => setSelectedGroupA(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="">(Auto-detect from dataset)</option>
                      {groups.map((g) => (
                        <option key={g.id} value={g.id}>
                          {g.name} [Code: {g.group_code}] {g.is_control ? "(Control)" : ""}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Group B (Treatment / Condition)</label>
                    <select
                      value={selectedGroupB}
                      onChange={(e) => setSelectedGroupB(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="">(Auto-detect from dataset)</option>
                      {groups.map((g) => (
                        <option key={g.id} value={g.id}>
                          {g.name} [Code: {g.group_code}]
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Measurement Column (Y) *</label>
                    <select
                      value={measurementColumn}
                      onChange={(e) => setMeasurementColumn(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      required
                    >
                      {columns.map((c) => (
                        <option key={c.name} value={c.name}>
                          {c.name} ({c.dtype})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Group Column (X)</label>
                    <select
                      value={groupColumn}
                      onChange={(e) => setGroupColumn(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="">(None)</option>
                      {columns.map((c) => (
                        <option key={c.name} value={c.name}>
                          {c.name} ({c.dtype})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Category</label>
                    <select
                      value={comparisonType}
                      onChange={(e: any) => {
                        const cat = e.target.value;
                        setComparisonType(cat);
                        if (cat === "anova") setMethod("one_way_anova");
                        else if (cat === "nonparametric") setMethod("mann_whitney");
                        else setMethod("welch_ttest");
                      }}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="two_group">Two-Group Parametric</option>
                      <option value="anova">Multi-Group ANOVA</option>
                      <option value="nonparametric">Non-Parametric</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Statistical Test Method *</label>
                    <select
                      value={method}
                      onChange={(e) => setMethod(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 font-medium text-cyan-400"
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
                          <option value="mann_whitney">Mann-Whitney U Test</option>
                          <option value="wilcoxon_signed_rank">Wilcoxon Signed-Rank Test (Paired)</option>
                          <option value="kruskal_wallis">Kruskal-Wallis H Test (Multi-Group)</option>
                        </>
                      )}
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-slate-300 mb-1">Significance Level (α)</label>
                    <select
                      value={alpha}
                      onChange={(e) => setAlpha(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="0.05">α = 0.05 (Default)</option>
                      <option value="0.01">α = 0.01 (Strict)</option>
                      <option value="0.10">α = 0.10 (Exploratory)</option>
                    </select>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
                  {comparisonType === "anova" || method === "kruskal_wallis" ? (
                    <div className="flex items-center space-x-2">
                      <span className="text-slate-300 font-medium">Post-Hoc Adjustment:</span>
                      <select
                        value={postHocMethod}
                        onChange={(e) => setPostHocMethod(e.target.value)}
                        className="px-3 py-1 rounded bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
                      >
                        <option value="none">None</option>
                        <option value="tukey">Tukey HSD</option>
                        <option value="bonferroni">Bonferroni</option>
                        <option value="holm">Holm</option>
                      </select>
                    </div>
                  ) : null}

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="pairedCheck"
                      checked={paired}
                      onChange={(e) => setPaired(e.target.checked)}
                      className="rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-0"
                    />
                    <label htmlFor="pairedCheck" className="text-slate-300 font-medium cursor-pointer">
                      Paired / Dependent Observations
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setIsCreateModalOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" disabled={executing}>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    {executing ? "Executing Analysis..." : "Run Group Comparison"}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* One-Factor Comparisons History */}
          {comparisons.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-300 flex items-center space-x-2">
                  <History className="w-4 h-4 text-cyan-400" />
                  <span>One-Factor Comparison Records ({comparisons.length})</span>
                </h4>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {comparisons.map((comp) => {
                  const isSelected = selectedComparison?.id === comp.id;
                  const stat = comp.result_summary?.statistical_result;
                  return (
                    <button
                      key={comp.id}
                      onClick={() => setSelectedComparisonId(comp.id)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        isSelected
                          ? "bg-cyan-950/40 border-cyan-500/80 ring-1 ring-cyan-500/30"
                          : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-bold text-xs text-slate-100">{comp.name}</div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            {comp.measurement_column} ({comp.comparison_type})
                          </div>
                        </div>
                        {stat?.is_significant ? (
                          <Badge variant="pass" className="text-[9px] px-1.5 py-0.5">
                            p &lt; α
                          </Badge>
                        ) : (
                          <Badge variant="neutral" className="text-[9px] px-1.5 py-0.5">
                            NS
                          </Badge>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Active Comparison View */}
          {selectedComparison ? (
            <StatisticalResultCard comparison={selectedComparison} />
          ) : (
            <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
              <FlaskConical className="w-10 h-10 text-cyan-500/50 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-slate-300">No Comparisons Run Yet</h4>
              <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
                Click "Run One-Factor Comparison" above to select experimental groups and execute a statistical test.
              </p>
              <Button
                size="sm"
                onClick={() => {
                  setIsCreateModalOpen(true);
                  setError(null);
                }}
              >
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Run One-Factor Comparison
              </Button>
            </Card>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. EXPERIMENTAL FACTORS MANAGEMENT VIEW                                   */}
      {/* ========================================================================= */}
      {activeSubTab === "factors" && (
        <FactorManagementPanel
          experimentId={experiment.id}
          factors={factors}
          onRefreshFactors={loadFactors}
        />
      )}
    </div>
  );
};
