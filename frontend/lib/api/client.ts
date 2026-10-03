const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  errorType: string;
  detail: string;

  constructor(status: number, errorType: string, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.errorType = errorType;
    this.detail = detail;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorType = "ApiError";
    let detail = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();
      if (data.error) errorType = data.error;
      if (data.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      // Failed to parse JSON error
    }

    throw new ApiError(response.status, errorType, detail);
  }

  return response.json();
}
