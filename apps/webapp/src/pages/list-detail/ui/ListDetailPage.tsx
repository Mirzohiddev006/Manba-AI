import { useState } from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import { useListDetail, useRemoveItem, useReorder } from '@/entities/list';
import { SortableList } from '@/features/reorder-items';
import { Button, Card, Spinner } from '@/shared/ui';

const GROUP_TITLES: Record<number, string> = {
  1: 'I. Normativ-huquqiy hujjatlar',
  2: 'II. Asosiy adabiyotlar',
  3: 'III. Internet manbalar',
};

export function ListDetailPage() {
  const { id } = useParams();
  const listId = Number(id);
  const nav = useNavigate();
  const { data, isLoading } = useListDetail(listId);
  const reorder = useReorder(listId);
  const removeItem = useRemoveItem(listId);
  const [manual, setManual] = useState(false);

  if (isLoading || !data) return <Spinner />;

  const groups = [1, 2, 3]
    .map((g) => ({ g, items: data.items.filter((i) => i.group_no === g) }))
    .filter(({ items }) => items.length);

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-tg-text">{data.title}</h1>
        <button className="text-sm text-tg-link" onClick={() => setManual((m) => !m)}>
          {manual ? 'Guruh ko\'rinishi' : 'Qo\'lda tartiblash'}
        </button>
      </div>
      {manual ? (
        <SortableList items={data.items} onReorder={(ids) => reorder.mutate(ids)} />
      ) : (
        groups.map(({ g, items }) => (
          <div key={g} className="space-y-2">
            <p className="text-sm font-semibold text-tg-hint">{GROUP_TITLES[g]}</p>
            {items.map((item, idx) => (
              <Card key={item.id} className="space-y-1">
                <p className="text-sm text-tg-text">
                  {idx + 1}. {item.source.formatted_text}
                </p>
                <div className="flex gap-3 text-xs">
                  <button
                    className="text-tg-link"
                    onClick={() => navigator.clipboard.writeText(item.source.formatted_text)}
                  >
                    📋 Nusxalash
                  </button>
                  <button className="text-tg-link" onClick={() => nav(`/edit/${item.source.id}`)}>
                    ✏️ Tahrirlash
                  </button>
                  <button className="text-red-500" onClick={() => removeItem.mutate(item.id)}>
                    🗑
                  </button>
                </div>
              </Card>
            ))}
          </div>
        ))
      )}
      <Button className="w-full" onClick={() => nav(`/export/${listId}`)}>📤 Eksport</Button>
    </div>
  );
}
