import { create } from 'zustand';

import { clearToken, getToken } from '@/shared/api/client';

export type Role = 'superadmin' | 'moderator' | 'content';

interface AuthState {
  role: Role | null;
  setRole: (r: Role) => void;
  logout: () => void;
  isAuthed: () => boolean;
}

export const useAuthStore = create<AuthState>((set) => ({
  role: (sessionStorage.getItem('admin_role') as Role) || null,
  setRole: (role) => {
    sessionStorage.setItem('admin_role', role);
    set({ role });
  },
  logout: () => {
    clearToken();
    sessionStorage.removeItem('admin_role');
    set({ role: null });
  },
  isAuthed: () => Boolean(getToken()),
}));

export const ROLE_LEVELS: Record<Role, number> = { superadmin: 3, moderator: 2, content: 1 };
