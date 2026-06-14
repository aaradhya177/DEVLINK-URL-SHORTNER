import { createContext } from "react";
import type { TokenResponse } from "../../api/types";

export interface AuthContextValue {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setTokens: (tokens: TokenResponse) => void;
  clearTokens: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
