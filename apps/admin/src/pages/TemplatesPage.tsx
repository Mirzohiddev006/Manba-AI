import { useState } from 'react';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { adminFetch } from '@/shared/api/client';
import { Badge, Button, Card, CardTitle, Textarea } from '@/shared/ui';

interface Template {
  id: number; source_type: string; lang: string;
  template_body: string; version: number; is_active: boolean;
}

const TYPES = ['book', 'book_many', 'journal_article', 'conference', 'dissertation',
  'abstract', 'legal', 'web', 'foreign_article'];

/** Jinja2 tahrirlovchi + sinov maydonchasi (TZ 6.1). */
export function TemplatesPage() {
  const qc = useQueryClient();
  const [sourceType, setSourceType] = useState('book');
  const [body, setBody] = useState('');
  const [preview, setPreview] = useState<string | null>(null);

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => adminFetch<Template[]>('/api/v1/admin/templates'),
  });

  const test = useMutation({
    mutationFn: () =>
      adminFetch<{ ok: boolean; preview?: string; error?: string }>(
        '/api/v1/admin/templates/test',
        { method: 'POST', body: JSON.stringify({ template_body: body, source_type: sourceType }) },
      ),
    onSuccess: (r) => setPreview(r.ok ? r.preview! : `Xato: ${r.error}`),
  });

  const save = useMutation({
    mutationFn: () =>
      adminFetch('/api/v1/admin/templates', {
        method: 'POST',
        body: JSON.stringify({ source_type: sourceType, lang: 'uz', template_body: body }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Format shablonlari</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Yangi versiya (Jinja2)</CardTitle>
          <select
            className="mb-2 h-9 w-full rounded-md border border-gray-300 px-2 text-sm"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
          >
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <Textarea rows={6} value={body} onChange={(e) => setBody(e.target.value)}
            placeholder="{{ authors|authors_sn }} {{ title }}. – {{ city }}: {{ publisher }}, {{ year }}." />
          <div className="mt-3 flex gap-2">
            <Button variant="outline" onClick={() => test.mutate()} disabled={!body}>
              ▶ Sinab ko'rish
            </Button>
            <Button onClick={() => save.mutate()} disabled={!body || preview?.startsWith('Xato')}>
              Saqlash (yangi versiya)
            </Button>
          </div>
          {preview && (
            <div className="mt-3 rounded-md bg-gray-50 p-3 text-sm">
              <p className="mb-1 text-xs text-gray-500">Sinov natijasi:</p>
              {preview}
            </div>
          )}
        </Card>
        <Card>
          <CardTitle>Mavjud shablonlar (versiyalangan)</CardTitle>
          <div className="max-h-96 space-y-2 overflow-auto">
            {templates?.map((t) => (
              <div key={t.id} className="rounded-md border border-gray-100 p-2 text-xs">
                <div className="mb-1 flex justify-between">
                  <Badge color="blue">{t.source_type} v{t.version}</Badge>
                  {t.is_active && <Badge color="green">faol</Badge>}
                </div>
                <code className="break-all text-gray-600">{t.template_body}</code>
              </div>
            ))}
            {!templates?.length && (
              <p className="text-sm text-gray-400">
                DB da shablon yo'q — citation-core standart shablonlari ishlaydi.
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
