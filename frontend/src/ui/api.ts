// Use relative path in production, or env variable if set
const API_BASE = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");

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

function buildQuery(params: Record<string, string | number | undefined | null>) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    searchParams.set(key, String(value));
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function listWorkflowPatients(
  token: string | null,
  params: {
    search?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }
) {
  const query = buildQuery(params as Record<string, string | number>);
  return apiGet(`/workflow/patients/${query}`, token);
}

export async function getPatientTimeline(
  token: string | null,
  patientId: string,
  params?: { date_from?: string; date_to?: string }
) {
  const query = buildQuery(params || {});
  return apiGet(`/workflow/patients/${patientId}/timeline/${query}`, token);
}

export async function login(username: string, password: string) {
  // Use relative path for production
  const isProd = (import.meta as any).env.PROD;
  const loginUrl = isProd 
    ? "/api/auth/token/" 
    : `${API_BASE.replace("/api", "")}/api/auth/token/`;
  const r = await fetch(loginUrl, {
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
