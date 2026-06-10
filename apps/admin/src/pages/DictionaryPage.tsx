import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { adminFetch } from '@/shared/api/client';
import { Badge, Button, Input, Table } from '@/shared/ui';

interface Word { id: number; word: string; script: string; category: string; status: string }

export function DictionaryPage() {
  const qc = useQueryClient();
  const [word, setWord] = useState('');
  const [category, setCategory] = useState('atama');
  const { data } = useQuery({
    queryKey: ['dictionary'],
    queryFn: () => adminFetch<Word[]>('/api/v1/admin/dictionary'),
  });
  const add = useMutation({
    mutationFn: () =>
      adminFetch(
        `/api/v1/admin/dictionary?word=${encodeURIComponent(word)}&category=${category}`,
        { method: 'POST' },
      ),
    onSuccess: () => {
      setWord('');
      void qc.invalidateQueries({ queryKey: ['dictionary'] });
    },
  });
  const moderate = useMutation({
    mutationFn: ({ id, approve }: { id: number; approve: boolean }) =>
      adminFetch(`/api/v1/admin/dictionary/${id}/moderate?approve=${approve}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dictionary'] }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Lug'at boshqaruvi</h1>
      <div className="flex gap-2">
        <Input className="w-64" placeholder="Yangi so'z…" value={word}
          onChange={(e) => setWord(e.target.value)} />
        <select className="h-9 rounded-md border border-gray-300 px-2 text-sm"
          value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="atama">Atama</option>
          <option value="atoqli_ot">Atoqli ot</option>
        </select>
        <Button onClick={() => add.mutate()} disabled={!word}>Qo'shish</Button>
      </div>
      <Table headers={['So\'z', 'Yozuv', 'Kategoriya', 'Holat', 'Moderatsiya']}>
        {data?.map((w) => (
          <tr key={w.id}>
            <td className="px-4 py-2 font-medium">{w.word}</td>
            <td className="px-4 py-2">{w.script}</td>
            <td className="px-4 py-2">{w.category}</td>
            <td className="px-4 py-2">
              <Badge color={w.status === 'active' ? 'green' : 'amber'}>{w.status}</Badge>
            </td>
            <td className="px-4 py-2">
              {w.status === 'pending' && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline"
                    onClick={() => moderate.mutate({ id: w.id, approve: true })}>✅</Button>
                  <Button size="sm" variant="destructive"
                    onClick={() => moderate.mutate({ id: w.id, approve: false })}>❌</Button>
                </div>
              )}
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
}
