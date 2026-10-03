import { DescriptiveStatisticsResult } from "../types/statistics";
import { apiRequest } from "./client";

export async function calculateDescriptiveStatistics(datasetId: string): Promise<DescriptiveStatisticsResult> {
  return apiRequest<DescriptiveStatisticsResult>(`/datasets/${datasetId}/statistics`, {
    method: "POST",
  });
}
