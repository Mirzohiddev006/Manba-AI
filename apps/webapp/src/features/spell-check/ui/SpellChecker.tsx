import { useState } from 'react';

import { useMutation } from '@tanstack/react-query';

import { apiFetch } from '@/shared/api/client';
import { Button, Card } from '@/shared/ui';

interface Issue { xato: string; taklif: string[]; pozitsiya: number }

/** Xatolar highlight + tooltip-taklif, qabul/rad (TZ 5.1). */
export function SpellChecker() {
  const [text, setText] = useState('');
  const [accepted, setAccepted] = useState<Set<number>>(new Set());
  const check = useMutation({
    mutationFn: (t: string) =>
      apiFetch<Issue[]>('/api/v1/spell/check', { method: 'POST', body: JSON.stringify({ text: t }) }),
    onSuccess: () => setAccepted(new Set()),
  });

  const issues = check.data ?? [];

  const applied = (): string => {
    let out = text;
    [...issues]
      .map((iss, i) => ({ iss, i }))
      .filter(({ i }) => accepted.has(i))
      .sort((a, b) => b.iss.pozitsiya - a.iss.pozitsiya)
      .forEach(({ iss }) => {
        out = out.slice(0, iss.pozitsiya) + iss.taklif[0] + out.slice(iss.pozitsiya + iss.xato.length);
      });
    return out;
  };

  const highlighted = () => {
    if (!issues.length) return text;
    const parts: { t: string; bad?: boolean; idx?: number }[] = [];
    let cursor = 0;
    issues.forEach((iss, idx) => {
      parts.push({ t: text.slice(cursor, iss.pozitsiya) });
      parts.push({ t: iss.xato, bad: true, idx });
      cursor = iss.pozitsiya + iss.xato.length;
    });
    parts.push({ t: text.slice(cursor) });
    return parts.map((p, i) =>
      p.bad ? (
        <mark
          key={i}
          title={`Taklif: ${issues[p.idx!].taklif.join(', ')}`}
          className={`rounded px-0.5 ${accepted.has(p.idx!) ? 'bg-green-200' : 'bg-red-200'}`}
          onClick={() =>
            setAccepted((prev) => {
              const next = new Set(prev);
              if (next.has(p.idx!)) next.delete(p.idx!);
              else next.add(p.idx!);
              return next;
            })
          }
        >
          {p.t}
        </mark>
      ) : (
        <span key={i}>{p.t}</span>
      ),
    );
  };

  return (
    <div className="space-y-4">
      <textarea
        className="min-h-32 w-full rounded-2xl bg-tg-secondary p-4 text-tg-text outline-none"
        placeholder="Tekshiriladigan matn…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <Button className="w-full" onClick={() => check.mutate(text)} disabled={!text.trim()}>
        Imloni tekshirish
      </Button>
      {check.isSuccess && issues.length === 0 && (
        <Card>✅ Imloviy xato topilmadi</Card>
      )}
      {issues.length > 0 && (
        <>
          <Card className="leading-relaxed">{highlighted()}</Card>
          <div className="flex gap-2">
            <Button className="flex-1" onClick={() => setAccepted(new Set(issues.map((_, i) => i)))}>
              ✅ Hammasini qabul
            </Button>
            <Button
              className="flex-1 bg-tg-secondary !text-tg-text"
              onClick={() => navigator.clipboard.writeText(applied())}
            >
              📋 Nusxalash
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
