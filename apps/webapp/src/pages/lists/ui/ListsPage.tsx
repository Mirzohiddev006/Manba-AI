import { useNavigate } from 'react-router-dom';

import { useCreateList, useLists } from '@/entities/list';
import { Button, Card, EmptyState, Spinner } from '@/shared/ui';

export function ListsPage() {
  const nav = useNavigate();
  const { data, isLoading } = useLists();
  const create = useCreateList();
  if (isLoading) return <Spinner />;
  return (
    <div className="space-y-3 p-4">
      <h1 className="text-xl font-semibold text-tg-text">📚 Ro'yxatlarim</h1>
      {!data?.length && <EmptyState text="Hozircha ro'yxat yo'q" />}
      {data?.map((lst) => (
        <Card key={lst.id} className="cursor-pointer">
          <div onClick={() => nav(`/lists/${lst.id}`)}>
            <div className="flex justify-between">
              <p className="font-medium text-tg-text">{lst.title}</p>
              <span className="text-sm text-tg-hint">{lst.items_count} manba</span>
            </div>
            {lst.updated_at && (
              <p className="text-xs text-tg-hint">
                {new Date(lst.updated_at).toLocaleDateString('uz')}
              </p>
            )}
          </div>
        </Card>
      ))}
      <Button className="w-full" onClick={() => create.mutate('Yangi ro\'yxat')}>
        ➕ Yangi ro'yxat
      </Button>
      <Button className="w-full bg-tg-secondary !text-tg-link" onClick={() => nav('/add')}>
        Manba qo'shish
      </Button>
    </div>
  );
}
