import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { adminFetch } from '@/shared/api/client';
import { Badge, Button, Card, CardTitle, Input, Table, Textarea } from '@/shared/ui';

export function PaymentsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Obuna va to'lovlar</h1>
      <Card>
        <CardTitle>To'lovlar jurnali</CardTitle>
        <p className="text-sm text-gray-500">
          Click / Payme / Stars webhook lari avtomatik qayd etiladi (payments jadvali).
          Tariflar CRUD va promo-kodlar — keyingi iteratsiya.
        </p>
      </Card>
    </div>
  );
}

export function BroadcastPage() {
  const [segment, setSegment] = useState('all');
  const [message, setMessage] = useState('');
  const send = useMutation({
    mutationFn: () =>
      adminFetch(
        `/api/v1/admin/broadcasts?segment=${segment}&message=${encodeURIComponent(message)}`,
        { method: 'POST' },
      ),
    onSuccess: () => setMessage(''),
  });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Broadcast</h1>
      <Card className="max-w-xl space-y-3">
        <select className="h-9 w-full rounded-md border border-gray-300 px-2 text-sm"
          value={segment} onChange={(e) => setSegment(e.target.value)}>
          <option value="all">Barcha foydalanuvchilar</option>
          <option value="premium">Faqat premium</option>
          <option value="inactive_30">30 kun faol emas</option>
        </select>
        <Textarea rows={4} value={message} placeholder="Xabar matni…"
          onChange={(e) => setMessage(e.target.value)} />
        <Button onClick={() => send.mutate()} disabled={!message}>
          📣 Navbatga qo'yish
        </Button>
        {send.isSuccess && <Badge color="green">Navbatga qo'yildi</Badge>}
      </Card>
    </div>
  );
}

interface FeedbackItem {
  id: number; user_id: number; text: string; status: string;
  admin_reply: string | null; created_at: string;
}

export function FeedbackPage() {
  const qc = useQueryClient();
  const [replies, setReplies] = useState<Record<number, string>>({});
  const { data } = useQuery({
    queryKey: ['feedback'],
    queryFn: () => adminFetch<FeedbackItem[]>('/api/v1/admin/feedback'),
  });
  const reply = useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) =>
      adminFetch(`/api/v1/admin/feedback/${id}/reply?reply=${encodeURIComponent(text)}`,
        { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['feedback'] }),
  });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Feedback</h1>
      {data?.map((f) => (
        <Card key={f.id} className="max-w-2xl">
          <div className="mb-2 flex justify-between">
            <Badge color={f.status === 'new' ? 'amber' : 'green'}>{f.status}</Badge>
            <span className="text-xs text-gray-400">{new Date(f.created_at).toLocaleString()}</span>
          </div>
          <p className="text-sm">{f.text}</p>
          {f.admin_reply ? (
            <p className="mt-2 rounded-md bg-gray-50 p-2 text-sm text-gray-600">↩ {f.admin_reply}</p>
          ) : (
            <div className="mt-3 flex gap-2">
              <Input placeholder="Javob…" value={replies[f.id] ?? ''}
                onChange={(e) => setReplies((r) => ({ ...r, [f.id]: e.target.value }))} />
              <Button size="sm" disabled={!replies[f.id]}
                onClick={() => reply.mutate({ id: f.id, text: replies[f.id] })}>
                Yuborish
              </Button>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}

interface AuditRow {
  id: number; admin_id: number | null; action: string; entity: string;
  payload: Record<string, unknown>; ip: string | null; at: string;
}

export function AuditPage() {
  const { data } = useQuery({
    queryKey: ['audit'],
    queryFn: () => adminFetch<AuditRow[]>('/api/v1/admin/audit'),
  });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Loglar va audit</h1>
      <Table headers={['Admin', 'Amal', 'Obyekt', 'Payload', 'IP', 'Vaqt']}>
        {data?.map((a) => (
          <tr key={a.id}>
            <td className="px-4 py-2">#{a.admin_id}</td>
            <td className="px-4 py-2"><Badge color="blue">{a.action}</Badge></td>
            <td className="px-4 py-2">{a.entity}</td>
            <td className="max-w-xs truncate px-4 py-2 font-mono text-xs">
              {JSON.stringify(a.payload)}
            </td>
            <td className="px-4 py-2 text-gray-500">{a.ip}</td>
            <td className="px-4 py-2 text-gray-500">{new Date(a.at).toLocaleString()}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}

export function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Sozlamalar</h1>
      <Card className="max-w-xl">
        <CardTitle>Global parametrlar</CardTitle>
        <p className="text-sm text-gray-500">
          Limitlar, LLM kaliti va texnik tanaffus rejimi AWS Secrets Manager /
          env orqali boshqariladi — bu yerda faqat ko'rsatiladi. O'zgartirish:
          ECS task definition yangilash (README → Deploy).
        </p>
      </Card>
    </div>
  );
}
