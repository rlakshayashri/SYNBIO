export interface DatasetProvenanceSummary {
  id: string;
  name: string;
  file_name: string;
}

export interface ExperimentProvenanceSummary {
  id: string;
  name: string;
}

export interface ComparisonProvenanceSummary {
  id: string;
  name: string;
  comparison_type: string;
  group_a_name?: string | null;
  group_b_name?: string | null;
  group_column?: string | null;
  measurement_column: string;
  method?: string | null;
}

export interface ResultProvenance {
  experiment_id: string;
  dataset_id: string;
  analysis_id: string;
  comparison_id?: string | null;
  software_version: string;
}

export interface ExperimentResultItem {
  analysis_id: string;
  analysis_type: string;
  created_at: string;
  software_version: string;
  dataset: DatasetProvenanceSummary;
  experiment: ExperimentProvenanceSummary;
  comparison?: ComparisonProvenanceSummary | null;
  provenance: ResultProvenance;
  parameters: Record<string, any>;
  result: Record<string, any>;
}

export interface ExperimentResultsResponse {
  experiment_id: string;
  experiment_name: string;
  total_results: number;
  results: ExperimentResultItem[];
}
