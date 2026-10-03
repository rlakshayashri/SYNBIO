export type AnalysisCategory =
  | "two_group"
  | "anova"
  | "nonparametric"
  | "correlation";

export type StatisticalMethod =
  | "student_ttest"
  | "welch_ttest"
  | "paired_ttest"
  | "one_way_anova"
  | "welch_anova"
  | "mann_whitney"
  | "wilcoxon_signed_rank"
  | "kruskal_wallis"
  | "pearson"
  | "spearman";

export type PostHocMethod = "none" | "tukey" | "bonferroni" | "holm";

export interface StatisticalAnalysisRequest {
  category: AnalysisCategory;
  method: StatisticalMethod;
  value_column: string;
  group_column?: string | null;
  value_column_2?: string | null;
  alpha?: number;
  post_hoc_method?: PostHocMethod;
  paired?: boolean;
}

export interface AssumptionResult {
  name: string;
  statistic?: number | null;
  p_value?: number | null;
  passed: boolean;
  details: string;
}

export interface EffectSizeResult {
  name: string;
  value?: number | null;
  interpretation?: string | null;
}

export interface ConfidenceIntervalResult {
  level: number;
  lower?: number | null;
  upper?: number | null;
  metric: string;
}

export interface PostHocResult {
  group1: string;
  group2: string;
  statistic?: number | null;
  p_raw?: number | null;
  p_adjusted?: number | null;
  correction_method: string;
  is_significant: boolean;
}

export interface StatisticalAnalysisResult {
  dataset_id?: string | null;
  test_name: string;
  category: AnalysisCategory;
  method: StatisticalMethod;
  variables: Record<string, any>;
  statistic_name: string;
  statistic_value?: number | null;
  p_value?: number | null;
  df?: any;
  alpha: number;
  is_significant: boolean;
  sample_size: Record<string, number> | number;
  effect_size?: EffectSizeResult | null;
  confidence_interval?: ConfidenceIntervalResult | null;
  assumptions: AssumptionResult[];
  post_hoc: PostHocResult[];
  warnings: string[];
  statement: string;
}
