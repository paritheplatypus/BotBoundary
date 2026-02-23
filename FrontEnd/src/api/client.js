// Simple API helper.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const resp = await fetch(url, {
    credentials: "include", // send/receive HttpOnly auth cookie
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
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
