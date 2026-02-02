// Use relative path in production, or env variable if set
const RAW_API_BASE: string =
  (import.meta as any).env.VITE_API_BASE ||
  ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");

export const API_BASE: string = (() => {
  const trimmed = RAW_API_BASE.replace(/\/$/, "");
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
})();

async function apiRequest(path: string, token: string | null, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // If body is FormData, let the browser set Content-Type (checking body in options is tricky for typed RequestInit)
  // But we can check if the caller passed a special flag or if we just detect it?
  // Easier: Allow caller to override Content-Type to undefined/null to suppress it.
  if (headers["Content-Type"] === "multipart/form-data") {
    delete headers["Content-Type"];
  }
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
    } catch { }
    const error = new Error(errorMsg) as Error & { status?: number };
    error.status = r.status;
    throw error;
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

export async function apiUpload(path: string, token: string | null, formData: FormData) {
  return apiRequest(path, token, {
    method: "POST",
    body: formData,
    headers: { "Content-Type": "multipart/form-data" }
  });
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
  const loginUrl = `${API_BASE}/auth/token/`;
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
