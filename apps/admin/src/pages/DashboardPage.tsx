import { useQuery } from '@tanstack/react-query';
import {
  Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

import { adminFetch } from '@/shared/api/client';
import { Card, CardTitle } from '@/shared/ui';

interface Dashboard {
  dau: number; wau: number; mau: number; total_users: number;
  sources_by_type: Record<string, number>;
  parse_methods: Record<string, number>;
  llm_cost_today_usd: number;
  revenue_month: number;
}

export function DashboardPage() {
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => adminFetch<Dashboard>('/api/v1/admin/dashboard'),
    refetchInterval: 60_000,
  });
  if (!data) return null;

  const typeData = Object.entries(data.sources_by_type).map(([name, value]) => ({ name, value }));
  const rulesShare = (() => {
    const rules = data.parse_methods['rules'] ?? 0;
    const total = Object.values(data.parse_methods).reduce((a, b) => a + b, 0);
    return total ? Math.round((rules / total) * 100) : 100;
  })();

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {[
          ['DAU', data.dau], ['WAU', data.wau], ['MAU', data.mau],
          ['Jami foydalanuvchi', data.total_users],
          ['LLM xarajati (bugun)', `$${data.llm_cost_today_usd.toFixed(2)}`],
        ].map(([label, value]) => (
          <Card key={String(label)}>
            <p className="text-xs text-gray-500">{label}</p>
            <p className="mt-1 text-2xl font-semibold">{value}</p>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Manbalar turlari bo'yicha</CardTitle>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={typeData}>
              <XAxis dataKey="name" fontSize={11} angle={-30} textAnchor="end" height={70} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Bar dataKey="value" fill="#111827" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <CardTitle>Quvur samaradorligi</CardTitle>
          <p className="text-3xl font-semibold">{rulesShare}%</p>
          <p className="text-sm text-gray-500">manbalar LLM siz (qoidaviy) tahlil qilindi</p>
          <p className="mt-4 text-3xl font-semibold">
            {(data.revenue_month / 100).toLocaleString('uz')} so'm
          </p>
          <p className="text-sm text-gray-500">oylik daromad</p>
        </Card>
      </div>
    </div>
  );
}
