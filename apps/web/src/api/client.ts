// Prefer same-origin `/api/v1` in Vite (proxied to backend) to avoid CORS issues.
const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  error: { code: string; message: string; details?: unknown[] } | null;
  trace_id?: string;
};

function getToken(): string | null {
  return localStorage.getItem("abcrm_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const json = (await res.json()) as ApiEnvelope<T>;
  if (!res.ok || !json.success) {
    throw new Error(json.error?.message || `Request failed (${res.status})`);
  }
  return json.data;
}

export function setAuthToken(token: string | null) {
  if (token) localStorage.setItem("abcrm_token", token);
  else localStorage.removeItem("abcrm_token");
}
