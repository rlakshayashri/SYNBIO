import React, { useState } from "react";
import { BarChart3, Play, AlertCircle, Info, RefreshCw } from "lucide-react";
import { ColumnMetadata } from "../../lib/types/dataset";
import {
  PlotType,
  AggregationType,
  VisualizationResult,
} from "../../lib/types/visualization";
import { generateVisualization } from "../../lib/api/visualization";
import { PlotlyChart } from "./PlotlyChart";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface VisualizationPanelProps {
  datasetId: string;
  columns: ColumnMetadata[];
}

export const VisualizationPanel: React.FC<VisualizationPanelProps> = ({
  datasetId,
  columns,
}) => {
  const [plotType, setPlotType] = useState<PlotType>("histogram");
  const [selectedColumn, setSelectedColumn] = useState<string>(
    columns.find((c) => c.dtype.includes("int") || c.dtype.includes("float"))?.name || columns[0]?.name || ""
  );
  const [xColumn, setXColumn] = useState<string>(
    columns.find((c) => c.dtype.includes("int") || c.dtype.includes("float"))?.name || columns[0]?.name || ""
  );
  const [yColumn, setYColumn] = useState<string>(
    columns.filter((c) => c.dtype.includes("int") || c.dtype.includes("float"))[1]?.name ||
      columns[0]?.name ||
      ""
  );
  const [groupColumn, setGroupColumn] = useState<string>("");
  const [categoryColumn, setCategoryColumn] = useState<string>(
    columns.find((c) => c.dtype === "object" || c.dtype === "string")?.name || columns[0]?.name || ""
  );
  const [valueColumn, setValueColumn] = useState<string>("");
  const [aggregation, setAggregation] = useState<AggregationType>("count");

  const [plotResult, setPlotResult] = useState<VisualizationResult | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const numericColumns = columns.filter(
    (c) => c.dtype.includes("int") || c.dtype.includes("float")
  );
  const categoricalColumns = columns.filter(
    (c) => c.dtype === "object" || c.dtype === "string" || !c.dtype.includes("float")
  );

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      let requestPayload: any = { plot_type: plotType };

      if (plotType === "histogram" || plotType === "boxplot") {
        if (!selectedColumn) {
          setError("Please select a numeric variable.");
          setIsGenerating(false);
          return;
        }
        requestPayload.column = selectedColumn;
      } else if (plotType === "scatter") {
        if (!xColumn || !yColumn) {
          setError("Please select both X and Y numeric variables.");
          setIsGenerating(false);
          return;
        }
        requestPayload.x_column = xColumn;
        requestPayload.y_column = yColumn;
        if (groupColumn) {
          requestPayload.group_column = groupColumn;
        }
      } else if (plotType === "bar") {
        if (!categoryColumn) {
          setError("Please select a category variable.");
          setIsGenerating(false);
          return;
        }
        requestPayload.category_column = categoryColumn;
        if (valueColumn) {
          requestPayload.value_column = valueColumn;
          requestPayload.aggregation = aggregation;
        }
      }

      const result = await generateVisualization(datasetId, requestPayload);
      setPlotResult(result);
    } catch (err: any) {
      setError(err.detail || "Unable to generate scientific plot. Please verify selected parameters.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h3 className="text-base font-bold text-slate-100">SCIENTIFIC VISUALIZATION</h3>
            <Badge variant="info">Module 4</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Exploratory graphical plots (Histogram, Box Plot, Scatter Plot, Bar Chart) prepared server-side by the Python scientific engine.
          </p>
        </div>
      </div>

      {/* Plot Type Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { id: "histogram", label: "Histogram", desc: "Distribution" },
          { id: "boxplot", label: "Box Plot", desc: "Spread & Outliers" },
          { id: "scatter", label: "Scatter Plot", desc: "Relationships" },
          { id: "bar", label: "Bar Chart", desc: "Category Summaries" },
        ].map((type) => (
          <button
            key={type.id}
            onClick={() => {
              setPlotType(type.id as PlotType);
              setError(null);
            }}
            className={`p-3 rounded-xl border text-left transition-all ${
              plotType === type.id
                ? "bg-cyan-950/40 border-cyan-500/80 text-white ring-1 ring-cyan-500/30"
                : "bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            <div className="font-semibold text-xs text-slate-200">{type.label}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">{type.desc}</div>
          </button>
        ))}
      </div>

      {/* Control Dropdowns */}
      <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl space-y-4">
        {error && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          {/* Controls for Histogram and Boxplot */}
          {(plotType === "histogram" || plotType === "boxplot") && (
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Select Numeric Variable *
              </label>
              <select
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {numericColumns.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name} ({col.dtype})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls for Scatter */}
          {plotType === "scatter" && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  X Variable (Numeric) *
                </label>
                <select
                  value={xColumn}
                  onChange={(e) => setXColumn(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  {numericColumns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Y Variable (Numeric) *
                </label>
                <select
                  value={yColumn}
                  onChange={(e) => setYColumn(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  {numericColumns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Group By (Categorical / Optional)
                </label>
                <select
                  value={groupColumn}
                  onChange={(e) => setGroupColumn(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  <option value="">None</option>
                  {columns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name} ({col.dtype})
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {/* Controls for Bar Chart */}
          {plotType === "bar" && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Category Variable *
                </label>
                <select
                  value={categoryColumn}
                  onChange={(e) => setCategoryColumn(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  {columns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name} ({col.dtype})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Value Variable (Numeric / Optional)
                </label>
                <select
                  value={valueColumn}
                  onChange={(e) => setValueColumn(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  <option value="">None (Count Mode)</option>
                  {numericColumns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>

              {valueColumn && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Aggregation Method
                  </label>
                  <select
                    value={aggregation}
                    onChange={(e) => setAggregation(e.target.value as AggregationType)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <option value="mean">Mean</option>
                    <option value="sum">Sum</option>
                    <option value="median">Median</option>
                    <option value="count">Count</option>
                  </select>
                </div>
              )}
            </>
          )}

          <div className={plotType === "histogram" || plotType === "boxplot" ? "sm:col-span-1" : ""}>
            <Button
              variant="primary"
              size="md"
              className="w-full"
              onClick={handleGenerate}
              isLoading={isGenerating}
            >
              <Play className="w-4 h-4 mr-2" />
              Generate Plot
            </Button>
          </div>
        </div>
      </div>

      {/* Render Chart Output */}
      {plotResult ? (
        <div className="space-y-3">
          <PlotlyChart data={plotResult} />

          {/* Observations & Excluded Missing Metadata Banner */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 bg-slate-950/40 border border-slate-800/80 px-3.5 py-2 rounded-lg">
            <div className="flex items-center space-x-2">
              <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
              <span>
                <strong className="text-slate-200">{plotResult.metadata.observations}</strong> observations plotted.
              </span>
            </div>
            {plotResult.metadata.missing_excluded > 0 && (
              <span className="text-amber-400/90 font-medium">
                {plotResult.metadata.missing_excluded} missing observation(s) excluded
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-slate-950/40 border border-slate-800 border-dashed rounded-xl p-8 text-center text-xs text-slate-400">
          <BarChart3 className="w-8 h-8 text-cyan-400/50 mx-auto mb-2" />
          <p className="font-semibold text-slate-300">No Visualization Generated Yet</p>
          <p className="text-[11px] text-slate-500 mt-1">
            Select a plot type and target variables above, then click <strong>Generate Plot</strong>.
          </p>
        </div>
      )}
    </div>
  );
};
