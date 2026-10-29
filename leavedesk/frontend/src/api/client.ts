import { parseProblem } from "./problem";

const SAFE = new Set(["GET", "HEAD", "OPTIONS"]);
const CSRF_KEY = "leavedesk.csrf";

export const signInPath = "/sign-in";

export function setCsrfToken(token: string | null): void {
  if (token) sessionStorage.setItem(CSRF_KEY, token);
  else sessionStorage.removeItem(CSRF_KEY);
}

/** Sign-in URL that returns the user to where they were (R2). */
export function signInUrl(returnTo: string): string {
  return `${signInPath}?next=${encodeURIComponent(returnTo)}`;
}

/** Only same-site relative paths are honoured as a return target. */
export function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

interface Options {
  method?: string;
  body?: unknown;
  /** Skip the 401 redirect (the sign-in call itself). */
  noRedirect?: boolean;
}

export async function api<T>(path: string, { method = "GET", body, noRedirect }: Options = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (!SAFE.has(method)) {
    const token = sessionStorage.getItem(CSRF_KEY);
    if (token) headers["X-CSRF-Token"] = token;
  }
  const res = await fetch(`/api/v1${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 401 && !noRedirect) {
    const here = window.location.pathname + window.location.search;
    if (window.location.pathname !== signInPath) window.location.assign(signInUrl(here));
  }
  if (!res.ok) throw await parseProblem(res);
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}
