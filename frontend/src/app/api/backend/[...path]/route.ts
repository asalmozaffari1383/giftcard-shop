import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = (process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
const ACCESS_COOKIE = "giftcard_access";
const REFRESH_COOKIE = "giftcard_refresh";
const secure = process.env.AUTH_COOKIE_SECURE === "true";

function setAuthCookies(response: NextResponse, access: string, refresh?: string) {
  const options = { httpOnly: true, secure, sameSite: "lax" as const, path: "/" };
  response.cookies.set(ACCESS_COOKIE, access, { ...options, maxAge: 15 * 60 });
  if (refresh) response.cookies.set(REFRESH_COOKIE, refresh, { ...options, maxAge: 7 * 24 * 60 * 60 });
}

function clearAuthCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { httpOnly: true, secure, sameSite: "lax", path: "/", maxAge: 0 });
}

async function callBackend(request: NextRequest, path: string, body: ArrayBuffer | undefined, access?: string, refreshBody?: string) {
  const headers = new Headers(request.headers);
  ["host", "cookie", "content-length", "authorization"].forEach((name) => headers.delete(name));
  if (access) headers.set("Authorization", `Bearer ${access}`);
  if (refreshBody) headers.set("Content-Type", "application/json");
  return fetch(`${API_URL}/${path}/${request.nextUrl.search}`, {
    method: request.method,
    headers,
    body: refreshBody || body,
    cache: "no-store",
    redirect: "manual",
  });
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path: segments } = await context.params;
  const path = segments.join("/");
  const cookieStore = await cookies();
  const access = cookieStore.get(ACCESS_COOKIE)?.value;
  const refresh = cookieStore.get(REFRESH_COOKIE)?.value;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();

  if (path === "auth/token/logout") {
    if (refresh) await callBackend(request, path, undefined, access, JSON.stringify({ refresh })).catch(() => undefined);
    const response = NextResponse.json({ detail: "logged out" });
    clearAuthCookies(response);
    return response;
  }

  let backendResponse = await callBackend(request, path, body, access);

  if (path === "auth/otp/verify" && backendResponse.ok) {
    const data = await backendResponse.json() as { access: string; refresh: string; user: unknown };
    const response = NextResponse.json({ user: data.user }, { status: backendResponse.status });
    setAuthCookies(response, data.access, data.refresh);
    return response;
  }

  let rotatedAccess: string | undefined;
  let rotatedRefresh: string | undefined;
  if (backendResponse.status === 401 && refresh && !path.startsWith("auth/")) {
    const refreshResponse = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
    if (refreshResponse.ok) {
      const tokens = await refreshResponse.json() as { access: string; refresh?: string };
      rotatedAccess = tokens.access;
      rotatedRefresh = tokens.refresh;
      backendResponse = await callBackend(request, path, body, rotatedAccess);
    }
  }

  const responseBody = await backendResponse.arrayBuffer();
  const response = new NextResponse(responseBody, {
    status: backendResponse.status,
    headers: { "Content-Type": backendResponse.headers.get("Content-Type") || "application/json" },
  });
  if (rotatedAccess) setAuthCookies(response, rotatedAccess, rotatedRefresh);
  if (backendResponse.status === 401 && refresh && !rotatedAccess) clearAuthCookies(response);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
