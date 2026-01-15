import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
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
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [user, setUser] = useState<AuthCtx["user"]>(null);
  const [isLoading, setIsLoading] = useState(false);

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
        setToken(null);
        localStorage.removeItem("token");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  const value = useMemo(() => ({
    token,
    setToken: (t: string | null) => {
      setToken(t);
      if (t) localStorage.setItem("token", t);
      else localStorage.removeItem("token");
    },
    logout: () => {
      setToken(null);
      localStorage.removeItem("token");
    },
    user,
    isLoading,
  }), [token, user, isLoading]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
