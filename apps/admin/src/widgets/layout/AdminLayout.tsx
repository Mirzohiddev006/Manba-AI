import { NavLink, Navigate, Outlet } from 'react-router-dom';

import { ROLE_LEVELS, useAuthStore, type Role } from '@/features/auth';
import { cn } from '@/shared/lib/cn';

const NAV: { to: string; label: string; minRole: Role }[] = [
  { to: '/', label: '📊 Dashboard', minRole: 'content' },
  { to: '/users', label: '👥 Foydalanuvchilar', minRole: 'moderator' },
  { to: '/payments', label: '💳 Obuna va to\'lovlar', minRole: 'moderator' },
  { to: '/templates', label: '📝 Format shablonlari', minRole: 'content' },
  { to: '/dictionary', label: '📖 Lug\'at', minRole: 'content' },
  { to: '/ai', label: '🤖 AI monitoring', minRole: 'moderator' },
  { to: '/broadcast', label: '📣 Broadcast', minRole: 'moderator' },
  { to: '/feedback', label: '💬 Feedback', minRole: 'moderator' },
  { to: '/audit', label: '🧾 Audit', minRole: 'superadmin' },
  { to: '/settings', label: '⚙️ Sozlamalar', minRole: 'superadmin' },
];

export function AdminLayout() {
  const { role, isAuthed, logout } = useAuthStore();
  if (!isAuthed()) return <Navigate to="/login" replace />;
  const level = role ? ROLE_LEVELS[role] : 0;

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r border-gray-200 bg-white p-4">
        <p className="mb-6 px-2 font-semibold">ManbaAI Admin</p>
        <nav className="space-y-1">
          {NAV.filter((n) => level >= ROLE_LEVELS[n.minRole]).map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                cn(
                  'block rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100',
                  isActive && 'bg-gray-900 text-white hover:bg-gray-900',
                )
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <button className="mt-8 px-3 text-sm text-gray-400 hover:text-red-600" onClick={logout}>
          Chiqish →
        </button>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
