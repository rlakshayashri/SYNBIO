export type ValidationStatus = "PASS" | "WARNING" | "ERROR";

export interface MissingValueCheck {
  column: string;
  missing_count: number;
  missing_percentage: number;
}

export interface DuplicateCheck {
  duplicate_count: number;
  duplicate_percentage: number;
}

export interface DataTypeCheck {
  column: string;
  detected_dtype: string;
}

export interface OutlierCheck {
  column: string;
  outlier_count: number;
  outlier_percentage: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ValidationSummary {
  missing_values: number;
  duplicate_rows: number;
  potential_outliers: number;
  empty_columns: number;
}

export interface ValidationChecks {
  missing_values: MissingValueCheck[];
  duplicates: DuplicateCheck;
  data_types: DataTypeCheck[];
  outliers: OutlierCheck[];
  empty_columns: string[];
}

export interface ValidationResult {
  dataset_id: string | null;
  row_count: number;
  column_count: number;
  overall_status: ValidationStatus;
  summary: ValidationSummary;
  checks: ValidationChecks;
  warnings: string[];
}
