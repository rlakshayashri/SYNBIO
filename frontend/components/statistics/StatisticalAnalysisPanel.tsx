import React, { useState } from "react";
import {
  FlaskConical,
  Play,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Info,
  Sliders,
  Scale,
  ShieldAlert,
} from "lucide-react";
import { ColumnMetadata } from "../../lib/types/dataset";
import {
  AnalysisCategory,
  StatisticalMethod,
  PostHocMethod,
  StatisticalAnalysisResult,
} from "../../lib/types/statistical_analysis";
import { executeStatisticalAnalysis } from "../../lib/api/statistical_analysis";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface StatisticalAnalysisPanelProps {
  datasetId: string;
  columns: ColumnMetadata[];
}

export const StatisticalAnalysisPanel: React.FC<StatisticalAnalysisPanelProps> = ({
  datasetId,
  columns,
}) => {
  const [category, setCategory] = useState<AnalysisCategory>("two_group");
  const [method, setMethod] = useState<StatisticalMethod>("welch_ttest");

  const numericColumns = columns.filter(
    (c) => c.dtype.includes("int") || c.dtype.includes("float")
  );
  const categoricalColumns = columns.filter(
    (c) => c.dtype === "object" || c.dtype === "string" || !c.dtype.includes("float")
  );

  const [valueColumn, setValueColumn] = useState<string>(
    numericColumns[0]?.name || columns[0]?.name || ""
  );
  const [groupColumn, setGroupColumn] = useState<string>(
    categoricalColumns[0]?.name || columns[0]?.name || ""
  );
  const [valueColumn2, setValueColumn2] = useState<string>(
    numericColumns[1]?.name || columns[0]?.name || ""
  );
  const [alpha, setAlpha] = useState<number>(0.05);
  const [postHocMethod, setPostHocMethod] = useState<PostHocMethod>("none");
  const [paired, setPaired] = useState<boolean>(false);

  const [result, setResult] = useState<StatisticalAnalysisResult | null>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Switch category handler resets defaults
  const handleCategoryChange = (newCat: AnalysisCategory) => {
    setCategory(newCat);
    setError(null);
    if (newCat === "two_group") {
      setMethod("welch_ttest");
      setPostHocMethod("none");
    } else if (newCat === "anova") {
      setMethod("one_way_anova");
      setPostHocMethod("tukey");
    } else if (newCat === "nonparametric") {
      setMethod("mann_whitney");
      setPostHocMethod("bonferroni");
    } else if (newCat === "correlation") {
      setMethod("pearson");
      setPostHocMethod("none");
    }
  };

  const handleRunAnalysis = async () => {
    setIsExecuting(true);
    setError(null);

    try {
      let requestPayload: any = {
        category,
        method,
        value_column: valueColumn,
        alpha,
        post_hoc_method: postHocMethod,
        paired,
      };

      if (category === "correlation") {
        if (!valueColumn || !valueColumn2) {
          setError("Please select two numeric variables for correlation.");
          setIsExecuting(false);
          return;
        }
        requestPayload.value_column_2 = valueColumn2;
      } else if (category === "two_group") {
        if (groupColumn) {
          requestPayload.group_column = groupColumn;
        } else if (valueColumn2) {
          requestPayload.value_column_2 = valueColumn2;
        } else {
          setError("Please select either a group column or a second numeric variable.");
          setIsExecuting(false);
          return;
        }
      } else if (category === "anova" || category === "nonparametric") {
        if (method === "kruskal_wallis" || category === "anova") {
          if (!groupColumn) {
            setError("Please select a categorical group column.");
            setIsExecuting(false);
            return;
          }
          requestPayload.group_column = groupColumn;
        } else {
          if (groupColumn) {
            requestPayload.group_column = groupColumn;
          } else if (valueColumn2) {
            requestPayload.value_column_2 = valueColumn2;
          }
        }
      }

      const res = await executeStatisticalAnalysis(datasetId, requestPayload);
      setResult(res);
    } catch (err: any) {
      setError(err.detail || "Unable to execute statistical analysis. Please check parameters.");
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h3 className="text-base font-bold text-slate-100">STATISTICAL HYPOTHESIS TESTING</h3>
            <Badge variant="info">Module 5</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic, assumption-checked statistical evidence (t-tests, ANOVA, non-parametric tests, and correlation) computed by SciPy & statsmodels.
          </p>
        </div>
      </div>

      {/* Category Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { id: "two_group", label: "Two-Group Comparison", desc: "t-tests (Student, Welch, Paired)" },
          { id: "anova", label: "Multi-Group ANOVA", desc: "One-Way & Welch ANOVA" },
          { id: "nonparametric", label: "Non-Parametric Tests", desc: "Mann-Whitney, Wilcoxon, Kruskal" },
          { id: "correlation", label: "Correlation Analysis", desc: "Pearson r & Spearman rho" },
        ].map((cat) => (
          <button
            key={cat.id}
            onClick={() => handleCategoryChange(cat.id as AnalysisCategory)}
            className={`p-3 rounded-xl border text-left transition-all ${
              category === cat.id
                ? "bg-cyan-950/40 border-cyan-500/80 text-white ring-1 ring-cyan-500/30"
                : "bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <div className="font-semibold text-xs text-slate-200">{cat.label}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">{cat.desc}</div>
          </button>
        ))}
      </div>

      {/* Parameter Control Form */}
      <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-4">
        {error && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Target Measurement Variable */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Measurement Variable (Y) *
            </label>
            <select
              value={valueColumn}
              onChange={(e) => setValueColumn(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {numericColumns.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.name} ({col.dtype})
                </option>
              ))}
            </select>
          </div>

          {/* Group Column or Second Numeric Variable */}
          {category === "correlation" ? (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Second Numeric Variable (X) *
              </label>
              <select
                value={valueColumn2}
                onChange={(e) => setValueColumn2(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {numericColumns.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name} ({col.dtype})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Group Column (Categorical)
              </label>
              <select
                value={groupColumn}
                onChange={(e) => setGroupColumn(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                <option value="">None (Use 2nd Numeric Variable)</option>
                {columns.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name} ({col.dtype})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Explicit Statistical Method Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Statistical Method *
            </label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as StatisticalMethod)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {category === "two_group" && (
                <>
                  <option value="welch_ttest">Welch's t-test (Unequal Variance)</option>
                  <option value="student_ttest">Student's t-test (Equal Variance)</option>
                  <option value="paired_ttest">Paired t-test (Dependent Samples)</option>
                </>
              )}
              {category === "anova" && (
                <>
                  <option value="one_way_anova">One-Way ANOVA</option>
                  <option value="welch_anova">Welch's ANOVA (Unequal Variance)</option>
                </>
              )}
              {category === "nonparametric" && (
                <>
                  <option value="mann_whitney">Mann-Whitney U Test (2 Groups)</option>
                  <option value="wilcoxon_signed_rank">Wilcoxon Signed-Rank Test (Paired 2 Groups)</option>
                  <option value="kruskal_wallis">Kruskal-Wallis H Test (Multi-Group)</option>
                </>
              )}
              {category === "correlation" && (
                <>
                  <option value="pearson">Pearson Correlation (Linear)</option>
                  <option value="spearman">Spearman Rank Correlation (Monotonic)</option>
                </>
              )}
            </select>
          </div>

          {/* Significance Alpha Threshold */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Significance Level (Alpha α)
            </label>
            <select
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value={0.01}>α = 0.01 (99% Confidence)</option>
              <option value={0.05}>α = 0.05 (95% Confidence - Default)</option>
              <option value={0.10}>α = 0.10 (90% Confidence)</option>
            </select>
          </div>

          {/* Multiple Comparison Adjustment */}
          {(category === "anova" || method === "kruskal_wallis") && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Post-Hoc Multiple Comparisons
              </label>
              <select
                value={postHocMethod}
                onChange={(e) => setPostHocMethod(e.target.value as PostHocMethod)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {category === "anova" && <option value="tukey">Tukey HSD Test</option>}
                <option value="bonferroni">Bonferroni Correction</option>
                <option value="holm">Holm-Bonferroni Correction</option>
                <option value="none">None (No Post-Hoc)</option>
              </select>
            </div>
          )}

          {/* Run Action Button */}
          <div className="flex items-end sm:col-span-1">
            <Button
              variant="primary"
              size="md"
              className="w-full"
              onClick={handleRunAnalysis}
              isLoading={isExecuting}
            >
              <Play className="w-4 h-4 mr-2" />
              Execute Analysis
            </Button>
          </div>
        </div>
      </div>

      {/* Analysis Output Section */}
      {result ? (
        <div className="space-y-6">
          {/* Main Evidence Summary Card */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
              <div>
                <h4 className="text-sm font-bold text-slate-100">{result.test_name}</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  α = {result.alpha} | Sample Size:{" "}
                  {typeof result.sample_size === "number"
                    ? `N = ${result.sample_size}`
                    : Object.entries(result.sample_size)
                        .map(([g, n]) => `${g} (N=${n})`)
                        .join(", ")}
                </p>
              </div>
              <Badge variant={result.is_significant ? "pass" : "neutral"}>
                {result.is_significant ? `Statistically Significant (p < ${result.alpha})` : `Not Significant (p ≥ ${result.alpha})`}
              </Badge>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-900 border border-slate-800/80 p-3 rounded-lg">
                <div className="text-[10px] text-slate-400 font-medium">TEST STATISTIC ({result.statistic_name})</div>
                <div className="text-base font-bold text-cyan-400 mt-0.5 font-mono">
                  {result.statistic_value !== null && result.statistic_value !== undefined
                    ? result.statistic_value.toFixed(4)
                    : "N/A"}
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800/80 p-3 rounded-lg">
                <div className="text-[10px] text-slate-400 font-medium">P-VALUE</div>
                <div className={`text-base font-bold mt-0.5 font-mono ${result.is_significant ? "text-emerald-400" : "text-slate-300"}`}>
                  {result.p_value !== null && result.p_value !== undefined
                    ? result.p_value < 0.0001
                      ? "< 0.0001"
                      : result.p_value.toFixed(4)
                    : "N/A"}
                </div>
              </div>

              {result.effect_size && (
                <div className="bg-slate-900 border border-slate-800/80 p-3 rounded-lg">
                  <div className="text-[10px] text-slate-400 font-medium">EFFECT SIZE ({result.effect_size.name})</div>
                  <div className="text-base font-bold text-amber-400 mt-0.5 font-mono">
                    {result.effect_size.value !== null && result.effect_size.value !== undefined
                      ? `${result.effect_size.value.toFixed(4)} (${result.effect_size.interpretation})`
                      : "N/A"}
                  </div>
                </div>
              )}

              {result.confidence_interval && (
                <div className="bg-slate-900 border border-slate-800/80 p-3 rounded-lg">
                  <div className="text-[10px] text-slate-400 font-medium">
                    {Math.round(result.confidence_interval.level * 100)}% CI ({result.confidence_interval.metric})
                  </div>
                  <div className="text-xs font-bold text-slate-200 mt-1 font-mono">
                    {typeof result.confidence_interval.lower === "number" && typeof result.confidence_interval.upper === "number"
                      ? `[${result.confidence_interval.lower.toFixed(4)}, ${result.confidence_interval.upper.toFixed(4)}]`
                      : "N/A"}
                  </div>
                </div>
              )}
            </div>

            {/* Factual Statement Callout Box */}
            <div className="bg-slate-900/90 border border-cyan-800/40 px-4 py-3 rounded-lg text-xs text-slate-200 flex items-start space-x-2.5">
              <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-cyan-300 block mb-0.5">Statistical Evidence Statement</strong>
                <p className="text-slate-300 leading-relaxed font-mono text-[11px]">{result.statement}</p>
              </div>
            </div>
          </div>

          {/* Assumption Checks Section */}
          {result.assumptions && result.assumptions.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center space-x-2">
                <Scale className="w-4 h-4 text-amber-400" />
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Statistical Assumption Checks
                </h4>
              </div>

              <div className="space-y-2">
                {result.assumptions.map((ass, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between p-3 bg-slate-900 border border-slate-800/80 rounded-lg text-xs"
                  >
                    <div className="flex items-start space-x-2.5">
                      {ass.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <span className="font-semibold text-slate-200">{ass.name}</span>
                        <p className="text-[11px] text-slate-400 mt-0.5">{ass.details}</p>
                      </div>
                    </div>
                    <Badge variant={ass.passed ? "pass" : "warning"}>
                      {ass.passed ? "Passed" : "Violated"}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Post-Hoc Multiple Comparisons Table */}
          {result.post_hoc && result.post_hoc.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Post-Hoc Pairwise Group Comparisons
                </h4>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2">Group 1</th>
                      <th className="px-3 py-2">Group 2</th>
                      <th className="px-3 py-2 font-mono">Statistic</th>
                      <th className="px-3 py-2 font-mono">Raw p</th>
                      <th className="px-3 py-2 font-mono">Adjusted p</th>
                      <th className="px-3 py-2">Correction Method</th>
                      <th className="px-3 py-2">Significance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {result.post_hoc.map((ph, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="px-3 py-2 font-semibold text-slate-200">{ph.group1}</td>
                        <td className="px-3 py-2 font-semibold text-slate-200">{ph.group2}</td>
                        <td className="px-3 py-2">{ph.statistic !== null && ph.statistic !== undefined ? ph.statistic.toFixed(4) : "N/A"}</td>
                        <td className="px-3 py-2">{ph.p_raw !== null && ph.p_raw !== undefined ? ph.p_raw.toFixed(4) : "N/A"}</td>
                        <td className="px-3 py-2 font-bold text-cyan-400">
                          {ph.p_adjusted !== null && ph.p_adjusted !== undefined ? ph.p_adjusted.toFixed(4) : "N/A"}
                        </td>
                        <td className="px-3 py-2 font-sans text-slate-400">{ph.correction_method}</td>
                        <td className="px-3 py-2 font-sans">
                          <Badge variant={ph.is_significant ? "pass" : "neutral"}>
                            {ph.is_significant ? "Significant" : "Not Significant"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Warnings & Limitation Notes */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="p-4 bg-amber-950/30 border border-amber-800/50 rounded-xl space-y-1.5 text-xs text-amber-300">
              <div className="flex items-center space-x-2 font-semibold text-amber-200">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Statistical Limitations & Warnings</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-300/90 pl-1">
                {result.warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-slate-950/40 border border-slate-800 border-dashed rounded-xl p-8 text-center text-xs text-slate-400">
          <FlaskConical className="w-8 h-8 text-cyan-400/50 mx-auto mb-2" />
          <p className="font-semibold text-slate-300">No Statistical Test Executed Yet</p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-md mx-auto">
            Select an analysis category, target variables, statistical method, and alpha threshold above, then click <strong>Execute Analysis</strong>.
          </p>
        </div>
      )}
    </div>
  );
};
