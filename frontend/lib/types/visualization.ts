export type PlotType = "histogram" | "boxplot" | "scatter" | "bar";
export type AggregationType = "count" | "mean" | "sum" | "median";

export interface VisualizationRequest {
  plot_type: PlotType;
  column?: string;
  x_column?: string;
  y_column?: string;
  group_column?: string;
  category_column?: string;
  value_column?: string;
  aggregation?: AggregationType;
}

export interface PlotTrace {
  name?: string;
  x: any[];
  y: any[];
  type: string;
  mode?: string;
}

export interface PlotMetadata {
  observations: number;
  missing_excluded: number;
  group_by?: string | null;
  aggregation?: string | null;
}

export interface VisualizationResult {
  dataset_id: string | null;
  plot_type: PlotType;
  title: string;
  x_axis: string;
  y_axis: string;
  traces: PlotTrace[];
  metadata: PlotMetadata;
}
