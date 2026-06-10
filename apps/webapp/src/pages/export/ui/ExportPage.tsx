import { useParams } from 'react-router-dom';

import { ExportPanel } from '@/features/export-list';

export function ExportPage() {
  const { id } = useParams();
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-xl font-semibold text-tg-text">📤 Eksport</h1>
      <ExportPanel listId={Number(id)} />
    </div>
  );
}
