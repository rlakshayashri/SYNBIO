export interface Dataset {
  id: string;
  project_id: string;
  name: string;
  file_name: string;
  file_type: string;
  file_size: number;
  row_count: number | null;
  column_count: number | null;
  storage_path: string;
  created_at: string;
  updated_at: string;
}

export interface ColumnMetadata {
  name: string;
  dtype: string;
  null_count: number;
  null_percentage: number;
}

export interface DatasetPreviewResponse {
  dataset_id: string;
  row_count: number;
  column_count: number;
  preview_rows: number;
  columns: ColumnMetadata[];
  data: Record<string, any>[];
}
