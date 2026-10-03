export interface ColumnStatistics {
  column: string;
  count: number;
  missing_count: number;
  mean: number | null;
  median: number | null;
  std: number | null;
  variance: number | null;
  min: number | null;
  max: number | null;
  q1: number | null;
  q2: number | null;
  q3: number | null;
  iqr: number | null;
  range: number | null;
  cv: number | null;
}

export interface DescriptiveStatisticsResult {
  dataset_id: string | null;
  row_count: number;
  numeric_column_count: number;
  non_numeric_column_count: number;
  statistics: ColumnStatistics[];
  skipped_columns: string[];
}
