"use client";

import React from "react";
import dynamic from "next/dynamic";
import { VisualizationResult } from "../../lib/types/visualization";

// Dynamically import Plotly with SSR disabled
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  data: VisualizationResult;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ data }) => {
  // Map backend PlotTrace data structures to Plotly trace objects
  const plotlyTraces = data.traces.map((trace) => {
    const isBox = data.plot_type === "boxplot" || trace.type === "box";
    const isHist = data.plot_type === "histogram" || trace.type === "histogram";
    const isBar = data.plot_type === "bar" || trace.type === "bar";

    return {
      name: trace.name || undefined,
      x: isBox ? undefined : trace.x,
      y: isBox ? (trace.y.length > 0 ? trace.y : trace.x) : trace.y.length > 0 ? trace.y : undefined,
      type: isBox ? "box" : isHist ? "histogram" : isBar ? "bar" : "scatter",
      mode: trace.mode || (data.plot_type === "scatter" ? "markers" : undefined),
      marker: {
        opacity: 0.8,
      },
    };
  });

  const layout = {
    title: {
      text: data.title,
      font: { color: "#f8fafc", size: 14 },
    },
    xaxis: {
      title: { text: data.x_axis, font: { color: "#94a3b8", size: 12 } },
      gridcolor: "#1e293b",
      zerolinecolor: "#334155",
      tickfont: { color: "#cbd5e1" },
    },
    yaxis: {
      title: { text: data.y_axis, font: { color: "#94a3b8", size: 12 } },
      gridcolor: "#1e293b",
      zerolinecolor: "#334155",
      tickfont: { color: "#cbd5e1" },
    },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#94a3b8" },
    autosize: true,
    margin: { t: 40, r: 20, l: 50, b: 40 },
    legend: {
      font: { color: "#cbd5e1", size: 11 },
      bgcolor: "rgba(15, 23, 42, 0.6)",
      bordercolor: "#334155",
      borderwidth: 1,
    },
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
  };

  return (
    <div className="w-full min-h-[380px] bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 flex justify-center items-center">
      <Plot
        data={plotlyTraces as any}
        layout={layout as any}
        config={config as any}
        style={{ width: "100%", height: "100%", minHeight: "360px" }}
      />
    </div>
  );
};
