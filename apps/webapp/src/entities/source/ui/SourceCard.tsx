import { Card } from '@/shared/ui';

import { TYPE_EMOJI, TYPE_NAMES, type Source } from '../model/types';

export function SourceCard({ source, onClick }: { source: Source; onClick?: () => void }) {
  const low = Object.entries(source.field_confidence ?? {}).filter(([, v]) => v < 0.6);
  return (
    <Card className="cursor-pointer space-y-2" >
      <div onClick={onClick} className="space-y-2">
        <div className="flex items-center justify-between text-sm text-tg-hint">
          <span>
            {TYPE_EMOJI[source.source_type]} {TYPE_NAMES[source.source_type]}
          </span>
          <span>{Math.round(source.confidence * 100)}%</span>
        </div>
        <p className="text-[15px] leading-snug text-tg-text">{source.formatted_text}</p>
        {low.length > 0 && (
          <p className="text-xs text-amber-600">
            ❓ Tekshiring: {low.map(([k]) => k).join(', ')}
          </p>
        )}
      </div>
    </Card>
  );
}
