import { apiRequest } from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
} from "./types";

export function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>(
    "/api/v1/auth/register",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    false,
  );
}

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    false,
  );
}

export function logout(refreshToken: string): Promise<undefined> {
  return apiRequest<undefined>(
    "/api/v1/auth/logout",
    {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    },
    false,
  );
}
