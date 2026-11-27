const TOKEN_KEY = "maqadi_token";
const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(status, code, message, existingItemId = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.existingItemId = existingItemId;
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 304) {
    return { notModified: true, etag: response.headers.get("ETag"), data: null };
  }

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const err = payload && payload.error ? payload.error : {};
    throw new ApiError(
      response.status,
      err.code || "unknown_error",
      err.message || "حدث خطأ غير متوقع",
      err.existing_item_id || null
    );
  }

  return {
    notModified: false,
    etag: response.headers.get("ETag"),
    data: payload,
  };
}

export async function createHousehold(body) {
  const res = await apiRequest("/households", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.data;
}

export async function joinHousehold(body) {
  const res = await apiRequest("/households/join", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.data;
}

export async function getMe() {
  const res = await apiRequest("/me");
  return res.data;
}
