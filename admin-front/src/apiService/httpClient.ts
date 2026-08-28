export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

type EnvelopeLike = { status?: string; error?: string };

export async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  const json = (await response.json().catch(() => ({}))) as T & EnvelopeLike;

  if (!response.ok || json.status === 'error') {
    throw new Error(json.error ?? `HTTP ${response.status}`);
  }

  return json;
}
