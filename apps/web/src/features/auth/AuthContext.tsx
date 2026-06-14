import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { configureApiClient } from "../../api/client";
import type { TokenResponse } from "../../api/types";
import { AuthContext, type AuthContextValue } from "./authContextValue";

const ACCESS_TOKEN_KEY = "devlink.accessToken";
const REFRESH_TOKEN_KEY = "devlink.refreshToken";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    localStorage.getItem(ACCESS_TOKEN_KEY),
  );
  const [refreshToken, setRefreshToken] = useState<string | null>(() =>
    localStorage.getItem(REFRESH_TOKEN_KEY),
  );

  const setTokens = useCallback((tokens: TokenResponse) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    setAccessToken(tokens.access_token);
    setRefreshToken(tokens.refresh_token);
  }, []);

  const clearTokens = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    setAccessToken(null);
    setRefreshToken(null);
  }, []);

  useEffect(() => {
    configureApiClient({
      getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
      getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
      setTokens,
      clearTokens,
    });
  }, [clearTokens, setTokens]);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      refreshToken,
      isAuthenticated: accessToken !== null,
      setTokens,
      clearTokens,
    }),
    [accessToken, clearTokens, refreshToken, setTokens],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
