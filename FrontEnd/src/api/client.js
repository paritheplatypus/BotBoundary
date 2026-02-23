// Simple API helper.
// Supports two auth transports:
//  - bearer (recommended when using API Gateway execute-api URL, i.e., no purchased domain)
//  - cookie  (when API is same-site with the frontend)

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const AUTH_MODE = (import.meta.env.VITE_AUTH_MODE || "bearer").toLowerCase();
const TOKEN_KEY = "bb_access_token";

export function getAuthToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  if (!token) return;
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch(path, options = {}) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const p = path.startsWith("/") ? path : `/${path}`;
  const url = `${base}${p}`;

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (AUTH_MODE === "bearer" || AUTH_MODE === "both") {
    const token = getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const resp = await fetch(url, {
    // Cookies are only needed in cookie/both mode.
    credentials: AUTH_MODE === "cookie" || AUTH_MODE === "both" ? "include" : "omit",
    headers,
    ...options,
  });

  const text = await resp.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!resp.ok) {
    const message = data?.detail || data?.message || `Request failed (${resp.status})`;
    throw new Error(message);
  }

  return data;
}
