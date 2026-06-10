const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export function getToken(): string | null {
  return sessionStorage.getItem('admin_token');
}

export function setToken(token: string): void {
  sessionStorage.setItem('admin_token', token);
}

export function clearToken(): void {
  sessionStorage.removeItem('admin_token');
}

export async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...init?.headers,
    },
  });
  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Sessiya tugadi');
  }
  if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
  return res.json() as Promise<T>;
}
