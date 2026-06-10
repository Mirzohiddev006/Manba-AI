import { useState } from 'react';

import { useMutation } from '@tanstack/react-query';

import { apiFetch } from '@/shared/api/client';
import { Button, Card } from '@/shared/ui';

export function ExportPanel({ listId }: { listId: number }) {
  const [grouping, setGrouping] = useState<'oak' | 'flat'>('oak');
  const [script, setScript] = useState<'latin' | 'cyrillic'>('latin');
  const exportMut = useMutation({
    mutationFn: async (fmt: string) => {
      const blob = await apiFetch<Blob>(`/api/v1/lists/${listId}/export`, {
        method: 'POST',
        body: JSON.stringify({ fmt, grouping, script, font_size: 14 }),
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fmt === 'docx' ? 'adabiyotlar_royxati.docx' : `royxat.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  const Toggle = ({ value, current, onSet, label }: {
    value: string; current: string; onSet: () => void; label: string;
  }) => (
    <button
      className={`flex-1 rounded-xl px-3 py-2 text-sm ${
        value === current ? 'bg-tg-button text-tg-buttonText' : 'bg-tg-secondary text-tg-text'
      }`}
      onClick={onSet}
    >
      {label}
    </button>
  );

  return (
    <Card className="space-y-3">
      <p className="text-sm text-tg-hint">Guruhlash</p>
      <div className="flex gap-2">
        <Toggle value="oak" current={grouping} onSet={() => setGrouping('oak')} label="OAK 3 guruh" />
        <Toggle value="flat" current={grouping} onSet={() => setGrouping('flat')} label="Yagona alifbo" />
      </div>
      <p className="text-sm text-tg-hint">Yozuv</p>
      <div className="flex gap-2">
        <Toggle value="latin" current={script} onSet={() => setScript('latin')} label="Lotin" />
        <Toggle value="cyrillic" current={script} onSet={() => setScript('cyrillic')} label="Кирилл" />
      </div>
      <div className="flex gap-2 pt-2">
        <Button className="flex-1" onClick={() => exportMut.mutate('docx')}>📄 Word (.docx)</Button>
        <Button className="flex-1 bg-tg-secondary !text-tg-text" onClick={() => exportMut.mutate('bib')}>
          BibTeX
        </Button>
      </div>
    </Card>
  );
}
