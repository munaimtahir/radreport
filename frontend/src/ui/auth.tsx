import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { apiGet, setTokenUpdateCallback } from "./api";

type AuthCtx = {
  token: string | null;
  refreshToken: string | null;
  setToken: (t: string | null, r?: string | null) => void;
  logout: () => void;
  user: {
    username: string;
    is_superuser: boolean;
    groups: string[];
  } | null;
  isLoading: boolean;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(localStorage.getItem("token"));
  const [refreshToken, setRefreshTokenState] = useState<string | null>(localStorage.getItem("refresh_token"));
  const [user, setUser] = useState<AuthCtx["user"]>(null);
  const [isLoading, setIsLoading] = useState(false);

  const setToken = useCallback((t: string | null, r: string | null = null) => {
    setTokenState(t);
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");

    // If r is explicitly passed as null/string, use it. If undefined, leave it alone? 
    // No, login passes it. Logout passes null. Refresh update passes undefined sometimes?
    // Let's make it explicit.
    if (r !== undefined) {
      setRefreshTokenState(r);
      if (r) localStorage.setItem("refresh_token", r);
      else localStorage.removeItem("refresh_token");
    }
  }, []);

  const logout = useCallback(() => {
    setTokenState(null);
    setRefreshTokenState(null);
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
  }, []);

  // Register token update callback from API
  useEffect(() => {
    setTokenUpdateCallback((newToken, newRefreshToken) => {
      // Update access token and partially update refresh token if provided
      setToken(newToken, newRefreshToken);
    });
  }, [setToken]);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    // Only fetch user if we don't have it? Or always?
    // If we just refreshed token, we might not need to refetch user, but it's safe.
    setIsLoading(true);
    apiGet("/auth/me/", token)
      .then((data: AuthCtx["user"]) => {
        setUser(data);
      })
      .catch(() => {
        // Only logout if even the refresh failed (which is handled in apiRequest).
        // But apiRequest throws error if refresh fails.
        // So here we catch that final error.
        setUser(null);
        logout();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token, logout]);

  const value = useMemo(() => ({
    token,
    refreshToken,
    setToken,
    logout,
    user,
    isLoading,
  }), [token, refreshToken, user, isLoading, setToken, logout]); // Added refreshToken to deps

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
