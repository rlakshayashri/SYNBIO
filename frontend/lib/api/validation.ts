import { ValidationResult } from "../types/validation";
import { apiRequest } from "./client";

export async function validateDataset(datasetId: string): Promise<ValidationResult> {
  return apiRequest<ValidationResult>(`/datasets/${datasetId}/validate`, {
    method: "POST",
  });
}
