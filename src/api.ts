function defaultBackendHttp(): string {
  // Prefer an explicit override.
  const env = (import.meta as any).env?.VITE_BACKEND_HTTP as string | undefined;
  if (env) return env;

  const { protocol, hostname, port } = window.location;

  // If running on the Vite dev server (517x), assume backend on :8080.
  // Otherwise, assume the backend is serving the app (same origin).
  if (port && port.startsWith("517")) {
    return `${protocol}//${hostname}:8080`;
  }

  return window.location.origin;
}

export const BACKEND_HTTP = defaultBackendHttp();

export function backendWsBase(): string {
  const http = BACKEND_HTTP;
  return http.replace(/^https:/, "wss:").replace(/^http:/, "ws:");
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BACKEND_HTTP}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND_HTTP}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}
