import { useEffect } from 'react';

import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import { AddSourcePage } from '@/pages/add-source';
import { EditSourcePage } from '@/pages/edit-source';
import { ExportPage } from '@/pages/export';
import { ListDetailPage } from '@/pages/list-detail';
import { ListsPage } from '@/pages/lists';
import { ProfilePage } from '@/pages/profile';
import { SpellPage } from '@/pages/spell';
import { tg } from '@/shared/lib/telegram';

function NavBar() {
  const nav = useNavigate();
  const { pathname } = useLocation();
  const tabs = [
    { path: '/', icon: '📚' },
    { path: '/add', icon: '➕' },
    { path: '/spell', icon: '🔍' },
    { path: '/profile', icon: '👤' },
  ];
  return (
    <nav className="fixed inset-x-0 bottom-0 flex justify-around border-t border-tg-secondary bg-tg-bg py-2">
      {tabs.map((tab) => (
        <button
          key={tab.path}
          className={`px-5 py-1 text-xl ${pathname === tab.path ? '' : 'opacity-40'}`}
          onClick={() => nav(tab.path)}
        >
          {tab.icon}
        </button>
      ))}
    </nav>
  );
}

export function App() {
  const nav = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    const webApp = tg();
    webApp?.ready();
    webApp?.expand();
  }, []);

  // Telegram BackButton: ichki sahifalarda ko'rinadi
  useEffect(() => {
    const webApp = tg();
    if (!webApp) return;
    if (pathname !== '/') {
      webApp.BackButton.show();
      webApp.BackButton.onClick(() => nav(-1));
    } else {
      webApp.BackButton.hide();
    }
  }, [pathname, nav]);

  return (
    <div className="min-h-screen bg-tg-bg pb-16">
      <Routes>
        <Route path="/" element={<ListsPage />} />
        <Route path="/lists/:id" element={<ListDetailPage />} />
        <Route path="/add" element={<AddSourcePage />} />
        <Route path="/edit/:id" element={<EditSourcePage />} />
        <Route path="/spell" element={<SpellPage />} />
        <Route path="/export/:id" element={<ExportPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
      <NavBar />
    </div>
  );
}
