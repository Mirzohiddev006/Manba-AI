import { useQuery } from '@tanstack/react-query';

import { apiFetch } from '@/shared/api/client';
import { Card, Spinner } from '@/shared/ui';

interface Me {
  first_name: string; lang: string; script: string; tariff: string;
  tariff_expires_at: string | null;
  usage_today: { sources: number; pdf: number };
}

export function ProfilePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => apiFetch<Me>('/api/v1/me'),
  });
  if (isLoading || !data) return <Spinner />;
  return (
    <div className="space-y-3 p-4">
      <h1 className="text-xl font-semibold text-tg-text">👤 Profil</h1>
      <Card>
        <p className="font-medium text-tg-text">{data.first_name}</p>
        <p className="text-sm text-tg-hint">
          Tarif: {data.tariff === 'premium' ? '⭐ Premium' : 'Bepul'}
          {data.tariff_expires_at &&
            ` (${new Date(data.tariff_expires_at).toLocaleDateString('uz')} gacha)`}
        </p>
      </Card>
      <Card>
        <p className="text-sm text-tg-hint">Bugungi foydalanish</p>
        <p className="text-tg-text">Manbalar: {data.usage_today.sources} / {data.tariff === 'premium' ? '∞' : 10}</p>
        <p className="text-tg-text">PDF: {data.usage_today.pdf} / {data.tariff === 'premium' ? '∞' : 1}</p>
      </Card>
    </div>
  );
}
