import { VisualizationRequest, VisualizationResult } from "../types/visualization";
import { apiRequest } from "./client";

export async function generateVisualization(
  datasetId: string,
  request: VisualizationRequest
): Promise<VisualizationResult> {
  return apiRequest<VisualizationResult>(`/datasets/${datasetId}/visualizations`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
