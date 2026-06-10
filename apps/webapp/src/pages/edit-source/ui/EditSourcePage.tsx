import { useParams } from 'react-router-dom';

import { usePatchSource, useSource, TYPE_NAMES, type SourceFields } from '@/entities/source';
import { Card, Spinner } from '@/shared/ui';

const FIELD_LABELS: Partial<Record<keyof SourceFields, string>> = {
  title: 'Sarlavha', subtitle: 'Izoh', city: 'Shahar', publisher: 'Nashriyot',
  year: 'Yil', pages_total: 'Sahifalar soni', pages_range: 'Sahifa oralig\'i',
  journal: 'Jurnal', collection: 'To\'plam', volume: 'Jild', issue: '№',
  url: 'URL', accessed_date: 'Murojaat sanasi', degree: 'Daraja',
  doc_number: 'Hujjat raqami', doc_date: 'Hujjat sanasi',
};

/** Maydon formasi + pastda JONLI formatlangan natija (har o'zgarishda preview). */
export function EditSourcePage() {
  const { id } = useParams();
  const sourceId = Number(id);
  const { data: source, isLoading } = useSource(sourceId);
  const patch = usePatchSource(sourceId);

  if (isLoading || !source) return <Spinner />;

  const update = (field: string, raw: string) => {
    const numeric = field === 'year' || field === 'pages_total';
    const value: unknown = numeric ? (raw ? Number(raw) : null) : raw;
    patch.mutate({ fields: { [field]: value } });
  };

  return (
    <div className="space-y-4 p-4 pb-32">
      <h1 className="text-lg font-semibold text-tg-text">
        ✏️ Tahrirlash — {TYPE_NAMES[source.source_type]}
      </h1>
      <div className="space-y-3">
        {(Object.keys(FIELD_LABELS) as (keyof SourceFields)[]).map((field) => (
          <label key={field} className="block">
            <span className="text-xs text-tg-hint">
              {FIELD_LABELS[field]}
              {(source.field_confidence?.[field] ?? 1) < 0.6 && ' ❓'}
            </span>
            <input
              className="mt-1 w-full rounded-xl bg-tg-secondary p-3 text-tg-text outline-none"
              defaultValue={String(source.fields[field] ?? '')}
              onBlur={(e) => update(field, e.target.value)}
            />
          </label>
        ))}
      </div>
      {/* Jonli preview — pastga mahkamlangan */}
      <div className="fixed inset-x-0 bottom-0 border-t border-tg-secondary bg-tg-bg p-4">
        <Card>
          <p className="text-xs text-tg-hint">Natija (jonli)</p>
          <p className="text-sm text-tg-text">
            {patch.data?.formatted_text ?? source.formatted_text}
          </p>
        </Card>
      </div>
    </div>
  );
}
