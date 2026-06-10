import { useParseMutation, SourceCard } from '@/entities/source';
import { useAddToList, useLists } from '@/entities/list';
import { haptic } from '@/shared/lib/telegram';
import { Button, Spinner } from '@/shared/ui';

import { useAddSourceStore } from '../model/store';

export function AddSourceForm() {
  const { text, setText } = useAddSourceStore();
  const parse = useParseMutation();
  const lists = useLists();
  const addToList = useAddToList();

  return (
    <div className="space-y-4">
      <textarea
        className="min-h-32 w-full rounded-2xl bg-tg-secondary p-4 text-tg-text outline-none"
        placeholder="Manba matni, URL, DOI yoki ISBN… (bir nechta qator — bir nechta manba)"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <Button
        className="w-full"
        disabled={text.trim().length < 3 || parse.isPending}
        onClick={() => {
          haptic('medium');
          parse.mutate(text);
        }}
      >
        Tahlil qilish
      </Button>
      {parse.isPending && <Spinner />}
      {/* Jonli natija preview */}
      {parse.data?.sources.map((s) => (
        <div key={s.id} className="space-y-2">
          <SourceCard source={s} />
          <Button
            className="w-full bg-tg-secondary !text-tg-link"
            onClick={() => {
              const target = lists.data?.[0];
              if (target) addToList.mutate({ listId: target.id, sourceId: s.id });
            }}
          >
            ➕ Ro'yxatga qo'shish
          </Button>
        </div>
      ))}
    </div>
  );
}
