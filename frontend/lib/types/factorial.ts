import { AssumptionResult, PostHocResult } from "./statistical_analysis";

export interface FactorLevel {
  id: string;
  factor_id: string;
  name: string;
  description?: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface FactorLevelCreate {
  name: string;
  description?: string | null;
  order_index?: number;
}

export interface ExperimentalFactor {
  id: string;
  experiment_id: string;
  name: string;
  description?: string | null;
  factor_type?: string | null;
  levels: FactorLevel[];
  created_at: string;
  updated_at: string;
}

export interface ExperimentalFactorCreate {
  name: string;
  description?: string | null;
  factor_type?: string | null;
  levels?: FactorLevelCreate[];
}

export interface AnovaEffectResult {
  effect_name: string;
  sum_of_squares: number;
  degrees_of_freedom: number;
  mean_square?: number | null;
  f_statistic?: number | null;
  p_value?: number | null;
  partial_eta_squared?: number | null;
  partial_eta_squared_ci?: [number, number] | null;
  effect_size_interpretation?: "negligible" | "small" | "medium" | "large" | null;
  is_significant: boolean;
}

export interface SimpleEffectResult {
  factor_name: string;
  at_factor_name: string;
  at_level: string;
  f_statistic?: number | null;
  p_value?: number | null;
  is_significant: boolean;
  degrees_of_freedom_num?: number | null;
  degrees_of_freedom_den?: number | null;
  pairwise_comparisons: PostHocResult[];
}

export interface TwoWayAnovaResult {
  model_formula: string;
  response_column: string;
  factor_a_column: string;
  factor_b_column: string;
  factor_a_levels: string[];
  factor_b_levels: string[];
  cell_sample_sizes: Record<string, number>;
  total_rows_input: number;
  valid_rows_used: number;
  excluded_rows_count: number;
  exclusion_reasons: Record<string, number>;
  design_balance: string;
  is_balanced: boolean;
  contrast_coding: string;
  anova_type: string;
  effects: Record<string, AnovaEffectResult>;
  assumptions: Record<string, AssumptionResult>;
  interaction_significant: boolean;
  post_hoc_method: string;
  post_hoc_comparisons: PostHocResult[];
  simple_effects: SimpleEffectResult[];
  warnings: string[];
  scientific_statement: string;
}

export interface FactorialComparison {
  id: string;
  experiment_id: string;
  analysis_id?: string | null;
  name: string;
  description?: string | null;
  status: string;
  dataset_id?: string | null;
  factor_a_id?: string | null;
  factor_b_id?: string | null;
  factor_a_column: string;
  factor_b_column: string;
  measurement_column: string;
  parameters: Record<string, any>;
  result_summary: Record<string, any>;
  two_way_anova_result?: TwoWayAnovaResult | null;
  created_at: string;
  updated_at: string;
}

export interface FactorialComparisonCreate {
  name: string;
  description?: string | null;
  dataset_id?: string | null;
  factor_a_id?: string | null;
  factor_b_id?: string | null;
  factor_a_column: string;
  factor_b_column: string;
  measurement_column: string;
  parameters?: Record<string, any>;
  alpha?: number;
  post_hoc_method?: string;
  check_assumptions?: boolean;
}

export interface FactorialComparisonUpdate {
  name?: string;
  description?: string | null;
  status?: string;
}
