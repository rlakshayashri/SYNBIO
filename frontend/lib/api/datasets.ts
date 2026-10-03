import { Dataset, DatasetPreviewResponse } from "../types/dataset";
import { apiRequest } from "./client";

export async function uploadDataset(
  projectId: string,
  file: File,
  name?: string
): Promise<Dataset> {
  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("file", file);
  if (name) {
    formData.append("name", name);
  }

  return apiRequest<Dataset>("/datasets/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getDatasets(projectId: string): Promise<Dataset[]> {
  return apiRequest<Dataset[]>(`/datasets?project_id=${encodeURIComponent(projectId)}`);
}

export async function getDataset(datasetId: string): Promise<Dataset> {
  return apiRequest<Dataset>(`/datasets/${datasetId}`);
}

export async function getDatasetPreview(
  datasetId: string,
  limit: number = 10
): Promise<DatasetPreviewResponse> {
  return apiRequest<DatasetPreviewResponse>(`/datasets/${datasetId}/preview?limit=${limit}`);
}
