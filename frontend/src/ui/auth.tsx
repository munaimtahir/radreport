import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { apiGet } from "./api";

type AuthCtx = {
  token: string | null;
  setToken: (t: string | null) => void;
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
  const [user, setUser] = useState<AuthCtx["user"]>(null);
  const [isLoading, setIsLoading] = useState(false);

  const setToken = useCallback((t: string | null) => {
    setTokenState(t);
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");
  }, []);

  const logout = useCallback(() => {
    setTokenState(null);
    localStorage.removeItem("token");
  }, []);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    apiGet("/auth/me/", token)
      .then((data: AuthCtx["user"]) => {
        setUser(data);
      })
      .catch(() => {
        setUser(null);
        logout();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token, logout]);

  const value = useMemo(() => ({
    token,
    setToken,
    logout,
    user,
    isLoading,
  }), [token, user, isLoading, setToken, logout]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
