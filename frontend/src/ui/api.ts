const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";

async function apiRequest(path: string, token: string | null, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const r = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!r.ok) {
    const text = await r.text();
    let errorMsg = text;
    try {
      const json = JSON.parse(text);
      errorMsg = json.detail || json.message || text;
    } catch {}
    throw new Error(errorMsg);
  }
  if (r.status === 204) return null;
  return r.json();
}

export async function apiGet(path: string, token: string | null) {
  return apiRequest(path, token, { method: "GET" });
}

export async function apiPost(path: string, token: string | null, body: any) {
  return apiRequest(path, token, { method: "POST", body: JSON.stringify(body) });
}

export async function apiPut(path: string, token: string | null, body: any) {
  return apiRequest(path, token, { method: "PUT", body: JSON.stringify(body) });
}

export async function apiPatch(path: string, token: string | null, body: any) {
  return apiRequest(path, token, { method: "PATCH", body: JSON.stringify(body) });
}

export async function apiDelete(path: string, token: string | null) {
  return apiRequest(path, token, { method: "DELETE" });
}

export async function login(username: string, password: string) {
  const r = await fetch(`${API_BASE.replace("/api", "")}/api/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text);
  }
  const data = await r.json();
  return data.access;
}
