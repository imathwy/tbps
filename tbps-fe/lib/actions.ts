"use server";

import {
  SimilarTheoremsRequest,
  SimilarTheoremsResponse,
  HealthResponse,
  ServerType,
  API_URLS,
} from "./api";

export async function findSimilarTheorems(
  request: SimilarTheoremsRequest,
  serverType: ServerType = "mock",
): Promise<SimilarTheoremsResponse> {
  const baseUrl = API_URLS[serverType];
  const response = await fetch(`${baseUrl}/find-similar-theorems`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function checkHealth(
  serverType: ServerType = "mock",
): Promise<HealthResponse> {
  const baseUrl = API_URLS[serverType];
  const response = await fetch(`${baseUrl}/health`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function getMockInfo(
  serverType: ServerType = "mock",
): Promise<any> {
  if (serverType !== "mock") {
    throw new Error("Mock info only available for mock server");
  }

  const baseUrl = API_URLS[serverType];
  const response = await fetch(`${baseUrl}/mock-info`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
