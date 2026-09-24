const API_URL = "/api/backend";

export class ApiError extends Error {
  constructor(public status: number, public data: unknown, message = "خطا در ارتباط با سرور") {
    super(message);
  }
}

function errorMessage(data: unknown) {
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
    const first = Object.values(record)[0];
    if (Array.isArray(first) && typeof first[0] === "string") return first[0];
    if (typeof first === "string") return first;
  }
  return "درخواست انجام نشد. دوباره تلاش کنید.";
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  const normalizedPath = path.length > 1 ? path.replace(/\/$/, "") : path;
  const response = await fetch(`${API_URL}${normalizedPath}`, { ...options, headers, cache: "no-store", credentials: "same-origin" });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(response.status, data, errorMessage(data));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function unwrapResults<T>(data: T[] | { results: T[] }) {
  return Array.isArray(data) ? data : data.results;
}
