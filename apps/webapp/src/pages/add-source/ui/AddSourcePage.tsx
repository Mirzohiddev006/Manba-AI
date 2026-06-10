import { AddSourceForm } from '@/features/add-source';

export function AddSourcePage() {
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-xl font-semibold text-tg-text">➕ Manba qo'shish</h1>
      <AddSourceForm />
    </div>
  );
}
