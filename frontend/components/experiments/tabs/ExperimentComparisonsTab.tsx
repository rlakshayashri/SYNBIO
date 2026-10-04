"use client";

import React, { useEffect, useState } from "react";
import {
  FlaskConical,
  Plus,
  Play,
  AlertCircle,
  Users,
  Database,
  History,
  CheckCircle2,
} from "lucide-react";
import { ColumnMetadata } from "../../../lib/types/dataset";
import {
  Comparison,
  ComparisonCreateRequest,
  ExperimentWorkspaceResponse,
} from "../../../lib/types/experiment";
import { runExperimentalComparison } from "../../../lib/api/experiments";
import { getDatasetPreview } from "../../../lib/api/datasets";
import { StatisticalResultCard } from "../comparison/StatisticalResultCard";
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

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedComparisonId, setSelectedComparisonId] = useState<string | null>(
    comparisons && comparisons.length > 0 ? comparisons[0].id : null
  );

  // Form State
  const [comparisonName, setComparisonName] = useState("Group Comparison Analysis");
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    attached_datasets[0]?.id || ""
  );
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [loadingColumns, setLoadingColumns] = useState(false);

  const [comparisonType, setComparisonType] = useState<"two_group" | "anova" | "nonparametric">(
    "two_group"
  );
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

  // Sync selected dataset & columns when dataset changes
  useEffect(() => {
    if (attached_datasets.length > 0 && !selectedDatasetId) {
      setSelectedDatasetId(attached_datasets[0].id);
    }
  }, [attached_datasets]);

  useEffect(() => {
    const loadColumns = async () => {
      if (!selectedDatasetId) return;
      setLoadingColumns(true);
      try {
        const preview = await getDatasetPreview(selectedDatasetId, 1);
        const cols = preview.columns || [];
        setColumns(cols);

        // Auto-select initial columns if empty
        const numeric = cols.filter((c) => c.dtype.includes("int") || c.dtype.includes("float"));
        const categorical = cols.filter((c) => !c.dtype.includes("float"));

        if (numeric.length > 0 && !measurementColumn) {
          setMeasurementColumn(numeric[0].name);
        }
        if (cols.length > 0 && !groupColumn) {
          const groupCol = cols.find((c) => c.name.toLowerCase().includes("group")) || cols[0];
          setGroupColumn(groupCol.name);
        }
      } catch {
        // Ignore preview error
      } finally {
        setLoadingColumns(false);
      }
    };

    loadColumns();
  }, [selectedDatasetId]);

  // Handle comparison submission
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

  const selectedComparison = comparisons.find((c) => c.id === selectedComparisonId) || comparisons[0];

  const numericColumns = columns.filter((c) => c.dtype.includes("int") || c.dtype.includes("float"));

  if (attached_datasets.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <Database className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Attached Datasets</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No datasets are attached to this experiment yet. Attach a dataset from the Datasets tab to create group comparisons.
        </p>
      </Card>
    );
  }

  if (groups.length === 0) {
    return (
      <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
        <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">No Experimental Groups</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No experimental groups are defined yet. Create at least two experimental groups (e.g. Control & Treatment) in the Groups tab.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <FlaskConical className="w-4 h-4 text-cyan-400" />
            <span>Group Comparisons & Statistical Analysis</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Contextualize experimental groups and execute transparent statistical hypothesis tests (t-tests, ANOVA, Mann-Whitney, Kruskal-Wallis).
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => {
            setIsCreateModalOpen(true);
            setError(null);
          }}
        >
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          Run New Comparison
        </Button>
      </div>

      {/* New Comparison Modal / Form */}
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

            {/* Framework & Method Selection */}
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

            {/* Optional Post-Hoc & Paired Flags */}
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

      {/* Comparisons History Bar */}
      {comparisons.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-300 flex items-center space-x-2">
              <History className="w-4 h-4 text-cyan-400" />
              <span>Experiment Comparison Records ({comparisons.length})</span>
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

      {/* Active Comparison Result View */}
      {selectedComparison ? (
        <StatisticalResultCard comparison={selectedComparison} />
      ) : (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <FlaskConical className="w-10 h-10 text-cyan-500/50 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">No Comparisons Run Yet</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
            Click "Run New Comparison" above to select experimental groups, set variables, and execute a statistical test.
          </p>
          <Button
            size="sm"
            onClick={() => {
              setIsCreateModalOpen(true);
              setError(null);
            }}
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            Run New Comparison
          </Button>
        </Card>
      )}
    </div>
  );
};
