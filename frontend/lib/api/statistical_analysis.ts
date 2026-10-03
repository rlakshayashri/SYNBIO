import {
  StatisticalAnalysisRequest,
  StatisticalAnalysisResult,
} from "../types/statistical_analysis";
import { apiRequest } from "./client";

export async function executeStatisticalAnalysis(
  datasetId: string,
  request: StatisticalAnalysisRequest
): Promise<StatisticalAnalysisResult> {
  return apiRequest<StatisticalAnalysisResult>(`/datasets/${datasetId}/statistical-analysis`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
