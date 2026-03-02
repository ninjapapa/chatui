function defaultBackendHttp(): string {
  // Prefer an explicit override.
  const env = (import.meta as any).env?.VITE_BACKEND_HTTP as string | undefined;
  if (env) return env;

  // If served by backend already (same origin), just use same origin.
  // Otherwise (Vite dev server on 517x), assume backend is on :8080 on same host.
  const { protocol, hostname, port } = window.location;

  // If we're already on 8080, use same origin.
  if (port === "8080") return `${protocol}//${hostname}:${port}`;

  // If no port (e.g. https default 443), also just use same origin.
  // (This might be a reverse proxy setup.)
  if (!port) return `${protocol}//${hostname}`;

  // Default dev assumption.
  return `${protocol}//${hostname}:8080`;
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
