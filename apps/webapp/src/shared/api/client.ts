import { API_BASE } from '@/shared/config';
import { initData } from '@/shared/lib/telegram';

let token: string | null = null;

async function authenticate(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/auth/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData() }),
  });
  if (!res.ok) throw new Error('Avtorizatsiya xatosi');
  const body = (await res.json()) as { access_token: string };
  token = body.access_token;
  return token;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!token) await authenticate();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    token = null;
    return apiFetch(path, init);
  }
  if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
  const ct = res.headers.get('content-type') ?? '';
  return (ct.includes('json') ? res.json() : res.blob()) as Promise<T>;
}
