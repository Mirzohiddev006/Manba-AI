import { StrictMode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { LoginForm } from '@/features/auth';
import { AiMonitoringPage } from '@/pages/AiMonitoringPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { DictionaryPage } from '@/pages/DictionaryPage';
import {
  AuditPage, BroadcastPage, FeedbackPage, PaymentsPage, SettingsPage,
} from '@/pages/SimplePages';
import { TemplatesPage } from '@/pages/TemplatesPage';
import { UsersPage } from '@/pages/UsersPage';
import { AdminLayout } from '@/widgets/layout/AdminLayout';

import './styles.css';

const client = new QueryClient({ defaultOptions: { queries: { retry: 1 } } });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={client}>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          <Route element={<AdminLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/payments" element={<PaymentsPage />} />
            <Route path="/templates" element={<TemplatesPage />} />
            <Route path="/dictionary" element={<DictionaryPage />} />
            <Route path="/ai" element={<AiMonitoringPage />} />
            <Route path="/broadcast" element={<BroadcastPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
);
