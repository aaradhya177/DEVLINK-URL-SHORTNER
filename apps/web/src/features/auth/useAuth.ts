import { useContext } from "react";
import { AuthContext, type AuthContextValue } from "./authContextValue";

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
