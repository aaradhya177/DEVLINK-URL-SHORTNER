import type { ApiErrorBody, TokenResponse } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  retryAfter: string | null;

  constructor(message: string, status: number, retryAfter: string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

export interface TokenStore {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  setTokens: (tokens: TokenResponse) => void;
  clearTokens: () => void;
}

let tokenStore: TokenStore | null = null;
let refreshInFlight: Promise<TokenResponse> | null = null;

export function configureApiClient(store: TokenStore): void {
  tokenStore = store;
}

export async function apiRequest<TResponse>(
  path: string,
  options: RequestInit = {},
  retryOnUnauthorized = true,
): Promise<TResponse> {
  const response = await fetchWithAuth(path, options);
  if (response.status === 401 && retryOnUnauthorized) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const retry = await fetchWithAuth(path, options);
      return parseResponse<TResponse>(retry);
    }
  }
  return parseResponse<TResponse>(response);
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function fetchWithAuth(
  path: string,
  options: RequestInit,
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const accessToken = tokenStore?.getAccessToken();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return fetch(apiUrl(path), {
    ...options,
    headers,
  });
}

async function parseResponse<TResponse>(response: Response): Promise<TResponse> {
  if (response.status === 204) {
    return undefined as TResponse;
  }

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const body = data as ApiErrorBody | null;
    const detail = body?.detail;
    const message =
      typeof detail === "string" ? detail : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, response.headers.get("Retry-After"));
  }
  return data as TResponse;
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = tokenStore?.getRefreshToken();
  if (!refreshToken || !tokenStore) {
    return false;
  }

  refreshInFlight ??= fetch(apiUrl("/api/v1/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(parseResponse<TokenResponse>)
    .finally(() => {
      refreshInFlight = null;
    });

  try {
    const tokens = await refreshInFlight;
    tokenStore.setTokens(tokens);
    return true;
  } catch {
    tokenStore.clearTokens();
    return false;
  }
}
