import { apiRequest } from "./client";
import { Dataset } from "../types/dataset";
import { ExperimentResultsResponse } from "../types/results";
import {
  Comparison,
  ComparisonCreateRequest,
  Experiment,
  ExperimentCreate,
  ExperimentUpdate,
  ExperimentWorkspaceResponse,
  ExperimentalGroup,
  ExperimentalGroupCreate,
  Replicate,
  ReplicateCreate,
} from "../types/experiment";

export async function createExperiment(data: ExperimentCreate): Promise<Experiment> {
  return apiRequest<Experiment>("/experiments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getExperiments(projectId?: string): Promise<Experiment[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest<Experiment[]>(`/experiments${query}`);
}

export async function getExperiment(id: string): Promise<Experiment> {
  return apiRequest<Experiment>(`/experiments/${id}`);
}

export async function getExperimentWorkspace(id: string): Promise<ExperimentWorkspaceResponse> {
  return apiRequest<ExperimentWorkspaceResponse>(`/experiments/${id}/workspace`);
}

export async function updateExperiment(id: string, data: ExperimentUpdate): Promise<Experiment> {
  return apiRequest<Experiment>(`/experiments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteExperiment(id: string): Promise<void> {
  return apiRequest<void>(`/experiments/${id}`, {
    method: "DELETE",
  });
}

export async function addExperimentalGroup(
  experimentId: string,
  data: ExperimentalGroupCreate
): Promise<ExperimentalGroup> {
  return apiRequest<ExperimentalGroup>(`/experiments/${experimentId}/groups`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function addReplicate(
  groupId: string,
  data: ReplicateCreate
): Promise<Replicate> {
  return apiRequest<Replicate>(`/experiments/groups/${groupId}/replicates`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function runExperimentalComparison(
  experimentId: string,
  request: ComparisonCreateRequest
): Promise<Comparison> {
  return apiRequest<Comparison>(`/experiments/${experimentId}/comparisons`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function attachDataset(
  experimentId: string,
  datasetId: string
): Promise<Dataset> {
  return apiRequest<Dataset>(`/experiments/${experimentId}/datasets/${datasetId}/attach`, {
    method: "POST",
  });
}

export async function detachDataset(
  experimentId: string,
  datasetId: string
): Promise<Dataset> {
  return apiRequest<Dataset>(`/experiments/${experimentId}/datasets/${datasetId}/detach`, {
    method: "DELETE",
  });
}

export async function getAttachedDatasets(experimentId: string): Promise<Dataset[]> {
  return apiRequest<Dataset[]>(`/experiments/${experimentId}/datasets`);
}

export async function uploadAndAttachDataset(
  experimentId: string,
  file: File,
  name?: string
): Promise<Dataset> {
  const formData = new FormData();
  formData.append("file", file);
  if (name) {
    formData.append("name", name);
  }

  return apiRequest<Dataset>(`/experiments/${experimentId}/datasets/upload`, {
    method: "POST",
    body: formData,
  });
}

export async function getExperimentResults(
  experimentId: string,
  analysisType?: string,
  datasetId?: string
): Promise<ExperimentResultsResponse> {
  const params = new URLSearchParams();
  if (analysisType) params.append("analysis_type", analysisType);
  if (datasetId) params.append("dataset_id", datasetId);

  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<ExperimentResultsResponse>(`/experiments/${experimentId}/results${query}`);
}

export async function downloadExperimentResultsExport(
  experimentId: string,
  format: "json" | "csv"
): Promise<void> {
  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const url = `${BASE_URL}/experiments/${experimentId}/results/export?format=${format}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Export failed with status ${response.status}`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `experiment_${experimentId}_results.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}


