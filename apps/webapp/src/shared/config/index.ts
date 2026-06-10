export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === '1' || import.meta.env.DEV;
