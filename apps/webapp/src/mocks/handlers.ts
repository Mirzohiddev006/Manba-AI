import { HttpResponse, http } from 'msw';

import type { Source } from '@/entities/source';

let nextId = 100;
const sources = new Map<number, Source>();
const lists = [
  { id: 1, title: 'Dissertatsiya', grouping_mode: 'oak', sort_mode: 'auto',
    items_count: 2, updated_at: new Date().toISOString() },
];
const items = [
  { id: 1, position: 0, group_no: 1, source: mockSource(1, 'legal',
    "O'zbekiston Respublikasining «Ta'lim to'g'risida»gi Qonuni. O'RQ-637-son, 23.09.2020 // Qonunchilik ma'lumotlari milliy bazasi, lex.uz") },
  { id: 2, position: 1, group_no: 2, source: mockSource(2, 'book',
    'Karimov A.A. Iqtisodiyot nazariyasi: Darslik. – Toshkent: Iqtisod-moliya, 2020. – 350 b.') },
];

function mockSource(id: number, type: Source['source_type'], text: string): Source {
  const s: Source = {
    id, raw_input: text, source_type: type,
    fields: { title: 'Iqtisodiyot nazariyasi', year: 2020, city: 'Toshkent' },
    formatted_text: text, confidence: 0.93, field_confidence: { title: 0.9 },
    parse_method: 'rules', warnings: [],
  };
  sources.set(id, s);
  return s;
}

export const handlers = [
  http.post('*/api/v1/auth/telegram', () =>
    HttpResponse.json({ access_token: 'mock-jwt', token_type: 'bearer' })),

  http.post('*/api/v1/sources/parse', async ({ request }) => {
    const { text } = (await request.json()) as { text: string };
    const out = text.split('\n').filter(Boolean).map((line) => {
      const id = nextId++;
      return mockSource(id, line.includes('//') ? 'journal_article' : 'book', line.trim());
    });
    return HttpResponse.json({ sources: out });
  }),

  http.get('*/api/v1/sources/:id', ({ params }) => {
    const s = sources.get(Number(params.id));
    return s ? HttpResponse.json(s) : new HttpResponse(null, { status: 404 });
  }),

  http.patch('*/api/v1/sources/:id', async ({ params, request }) => {
    const s = sources.get(Number(params.id));
    if (!s) return new HttpResponse(null, { status: 404 });
    const patch = (await request.json()) as { fields?: Record<string, unknown> };
    s.fields = { ...s.fields, ...patch.fields };
    s.formatted_text = `${s.fields.title ?? ''} (yangilandi: ${JSON.stringify(patch.fields)})`;
    return HttpResponse.json(s);
  }),

  http.get('*/api/v1/lists', () => HttpResponse.json(lists)),
  http.post('*/api/v1/lists', () => {
    const lst = { id: nextId++, title: "Yangi ro'yxat", grouping_mode: 'oak',
      sort_mode: 'auto', items_count: 0, updated_at: new Date().toISOString() };
    lists.push(lst);
    return HttpResponse.json(lst, { status: 201 });
  }),
  http.get('*/api/v1/lists/:id', ({ params }) =>
    HttpResponse.json({ ...lists[0], id: Number(params.id), items })),
  http.post('*/api/v1/lists/:id/items/:sid', () => new HttpResponse(null, { status: 201 })),
  http.post('*/api/v1/lists/:id/reorder', () => new HttpResponse(null, { status: 204 })),
  http.delete('*/api/v1/lists/:id/items/:iid', () => new HttpResponse(null, { status: 204 })),

  http.post('*/api/v1/spell/check', async ({ request }) => {
    const { text } = (await request.json()) as { text: string };
    const idx = text.indexOf('tehnologiya');
    return HttpResponse.json(
      idx >= 0 ? [{ xato: 'tehnologiya', taklif: ['texnologiya'], pozitsiya: idx }] : [],
    );
  }),

  http.get('*/api/v1/me', () =>
    HttpResponse.json({
      first_name: 'Mirzohid', lang: 'uz', script: 'latin', tariff: 'free',
      tariff_expires_at: null, usage_today: { sources: 3, pdf: 0 },
    })),
];
