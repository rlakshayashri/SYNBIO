export interface ExperimentReportHeader {
  experiment_id: string;
  experiment_name: string;
  description: string | null;
  objective: string | null;
  status: string;
  organism: string | null;
  condition_type: string | null;
  assay_type: string | null;
  target_gene: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  report_generated_at: string;
  software_version: string;
}

export interface GroupReplicateReportItem {
  id: string;
  replicate_name: string;
  sample_identifier: string | null;
  row_index: number | null;
  replicate_type: string;
  metadata_payload: Record<string, any>;
}

export interface ExperimentalGroupReportItem {
  id: string;
  name: string;
  group_code: string;
  is_control: boolean;
  description: string | null;
  metadata_payload: Record<string, any>;
  replicates: GroupReplicateReportItem[];
}

export interface ExperimentalContextReport {
  experiment_name: string;
  description: string | null;
  objective: string | null;
  status: string;
  organism: string | null;
  condition_type: string | null;
  assay_type: string | null;
  target_gene: string | null;
  notes: string | null;
  groups: ExperimentalGroupReportItem[];
}

export interface DatasetReportItem {
  dataset_id: string;
  dataset_name: string;
  file_name: string;
  file_type: string;
  file_size: number;
  row_count: number | null;
  column_count: number | null;
  created_at: string;
  has_validation: boolean;
}

export interface DataQualityReportItem {
  analysis_id: string;
  dataset_id: string;
  dataset_name: string;
  created_at: string;
  missing_values: Record<string, any> | null;
  duplicate_rows: number | null;
  detected_data_types: Record<string, any> | null;
  empty_columns: string[] | null;
  outliers_summary: Record<string, any> | null;
  validation_passed: boolean | null;
}

export interface DescriptiveStatisticsReportItem {
  analysis_id: string;
  dataset_id: string;
  dataset_name: string;
  created_at: string;
  column_name: string;
  count: number | null;
  missing_count: number | null;
  mean: number | null;
  median: number | null;
  std_dev: number | null;
  variance: number | null;
  min_val: number | null;
  max_val: number | null;
  range_val: number | null;
  q1: number | null;
  q2: number | null;
  q3: number | null;
  iqr: number | null;
  cv: number | null;
}

export interface VisualizationReportItem {
  analysis_id: string;
  dataset_id: string;
  dataset_name: string;
  created_at: string;
  visualization_type: string;
  configuration: Record<string, any>;
}

export interface ComparisonReportItem {
  comparison_id: string;
  comparison_name: string;
  comparison_type: string;
  dataset_id: string | null;
  dataset_name: string | null;
  group_a_name: string | null;
  group_b_name: string | null;
  group_column: string | null;
  measurement_column: string;
  statistical_method: string | null;
  parameters: Record<string, any>;
  created_at: string;
}

export interface StatisticalResultReportItem {
  analysis_id: string;
  analysis_type: string;
  dataset_id: string;
  dataset_name: string;
  comparison_id: string | null;
  created_at: string;
  test_name: string | null;
  statistic_name: string | null;
  statistic_value: number | null;
  p_value: number | null;
  degrees_of_freedom: number | null;
  effect_size_name: string | null;
  effect_size_value: number | null;
  confidence_interval: number[] | null;
  is_significant: boolean | null;
  assumption_checks: Record<string, any> | null;
  raw_result: Record<string, any>;
}

export interface ProvenanceReportItem {
  section: string;
  analysis_id: string | null;
  analysis_type: string | null;
  comparison_id: string | null;
  dataset_id: string | null;
  dataset_name: string | null;
  experiment_id: string;
  software_version: string;
  created_at: string;
}

export interface ExperimentReport {
  metadata: ExperimentReportHeader;
  experimental_context: ExperimentalContextReport;
  datasets: DatasetReportItem[];
  data_quality: DataQualityReportItem[];
  descriptive_statistics: DescriptiveStatisticsReportItem[];
  visualizations: VisualizationReportItem[];
  comparisons: ComparisonReportItem[];
  statistical_results: StatisticalResultReportItem[];
  provenance: ProvenanceReportItem[];
  generated_at: string;
  disclaimer: string;
}
