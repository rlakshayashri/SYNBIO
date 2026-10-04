import { Dataset } from "./dataset";
import { StatisticalAnalysisResult } from "./statistical_analysis";
import { DescriptiveStatisticsResult } from "./statistics";

export interface Replicate {
  id: string;
  group_id: string;
  replicate_name: string;
  sample_identifier?: string | null;
  row_index?: number | null;
  replicate_type: string;
  metadata_payload: Record<string, any>;
  created_at: string;
}

export interface ReplicateCreate {
  replicate_name: string;
  sample_identifier?: string | null;
  row_index?: number | null;
  replicate_type?: string;
  metadata_payload?: Record<string, any>;
}

export interface ExperimentalGroup {
  id: string;
  experiment_id: string;
  name: string;
  group_code: string;
  is_control: boolean;
  description?: string | null;
  metadata_payload: Record<string, any>;
  replicates: Replicate[];
  created_at: string;
  updated_at: string;
}

export interface ExperimentalGroupCreate {
  name: string;
  group_code: string;
  is_control?: boolean;
  description?: string | null;
  metadata_payload?: Record<string, any>;
  replicates?: ReplicateCreate[];
}

export interface GroupDataSummary {
  group_id?: string | null;
  group_name: string;
  group_code?: string | null;
  is_control: boolean;
  sample_size_total: number;
  sample_size_valid: number;
  missing_count: number;
  descriptive_stats?: DescriptiveStatisticsResult | null;
}

export interface Comparison {
  id: string;
  experiment_id: string;
  analysis_id?: string | null;
  name: string;
  comparison_type: string;
  group_a_id?: string | null;
  group_b_id?: string | null;
  measurement_column: string;
  group_column?: string | null;
  parameters: Record<string, any>;
  result_summary: {
    statistical_result?: StatisticalAnalysisResult;
    group_summaries?: GroupDataSummary[];
  };
  created_at: string;
}

export interface ComparisonCreateRequest {
  name: string;
  comparison_type: string;
  group_a_id?: string | null;
  group_b_id?: string | null;
  measurement_column: string;
  group_column?: string | null;
  category?: string;
  method?: string;
  alpha?: number;
  post_hoc_method?: string;
  paired?: boolean;
}

export interface AnalysisRecord {
  id: string;
  dataset_id: string;
  experiment_id?: string | null;
  analysis_type: string;
  parameters: Record<string, any>;
  result: Record<string, any>;
  software_version: string;
  created_at: string;
}

export interface Experiment {
  id: string;
  project_id: string;
  dataset_id?: string | null;
  name: string;
  description?: string | null;
  status?: string;
  objective?: string | null;
  organism?: string | null;
  condition_type?: string | null;
  notes?: string | null;
  groups: ExperimentalGroup[];
  comparisons: Comparison[];
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  project_id: string;
  dataset_id?: string | null;
  name: string;
  description?: string | null;
  status?: string;
  objective?: string | null;
  organism?: string | null;
  condition_type?: string | null;
  notes?: string | null;
  groups?: ExperimentalGroupCreate[];
}

export interface ExperimentUpdate {
  name?: string;
  description?: string;
  status?: string;
  objective?: string | null;
  organism?: string;
  condition_type?: string;
  notes?: string;
  dataset_id?: string | null;
}

export interface ExperimentWorkspaceResponse {
  experiment: Experiment;
  attached_datasets: Dataset[];
  groups: ExperimentalGroup[];
  comparisons: Comparison[];
  analyses: AnalysisRecord[];
}

