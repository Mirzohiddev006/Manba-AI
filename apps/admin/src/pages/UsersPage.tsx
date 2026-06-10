import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { adminFetch } from '@/shared/api/client';
import { Badge, Button, Input, Table } from '@/shared/ui';

interface UserRow {
  id: number; tg_id: number; username: string | null; first_name: string | null;
  lang: string; tariff: string; is_blocked: boolean; created_at: string;
}

export function UsersPage() {
  const [q, setQ] = useState('');
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ['users', q],
    queryFn: () => adminFetch<{ total: number; items: UserRow[] }>(
      `/api/v1/admin/users?q=${encodeURIComponent(q)}`),
  });
  const block = useMutation({
    mutationFn: ({ id, blocked }: { id: number; blocked: boolean }) =>
      adminFetch(`/api/v1/admin/users/${id}/block?blocked=${blocked}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });
  const premium = useMutation({
    mutationFn: (id: number) =>
      adminFetch(`/api/v1/admin/users/${id}/grant-premium?days=30`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Foydalanuvchilar ({data?.total ?? 0})</h1>
        <Input
          className="w-64" placeholder="Qidirish…" value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <Table headers={['ID', 'Foydalanuvchi', 'Til', 'Tarif', 'Holat', 'Amallar']}>
        {data?.items.map((u) => (
          <tr key={u.id}>
            <td className="px-4 py-2 text-gray-500">{u.tg_id}</td>
            <td className="px-4 py-2">{u.first_name} {u.username && `(@${u.username})`}</td>
            <td className="px-4 py-2">{u.lang}</td>
            <td className="px-4 py-2">
              <Badge color={u.tariff === 'premium' ? 'amber' : 'gray'}>{u.tariff}</Badge>
            </td>
            <td className="px-4 py-2">
              <Badge color={u.is_blocked ? 'red' : 'green'}>
                {u.is_blocked ? 'Bloklangan' : 'Faol'}
              </Badge>
            </td>
            <td className="px-4 py-2">
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => premium.mutate(u.id)}>
                  ⭐ 30 kun
                </Button>
                <Button
                  size="sm" variant={u.is_blocked ? 'outline' : 'destructive'}
                  onClick={() => block.mutate({ id: u.id, blocked: !u.is_blocked })}
                >
                  {u.is_blocked ? 'Ochish' : 'Bloklash'}
                </Button>
              </div>
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
}
