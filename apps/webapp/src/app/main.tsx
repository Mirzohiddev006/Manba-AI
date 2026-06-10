import { StrictMode } from 'react';

import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { USE_MOCKS } from '@/shared/config';

import { App } from './App';
import { QueryProvider } from './providers/QueryProvider';
import './styles.css';

async function bootstrap() {
  if (USE_MOCKS) {
    const { worker } = await import('@/mocks/browser');
    await worker.start({ onUnhandledRequest: 'bypass' });
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <BrowserRouter>
        <QueryProvider>
          <App />
        </QueryProvider>
      </BrowserRouter>
    </StrictMode>,
  );
}

void bootstrap();
