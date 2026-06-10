import { SpellChecker } from '@/features/spell-check';

export function SpellPage() {
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-xl font-semibold text-tg-text">🔍 Imlo tekshiruvi</h1>
      <SpellChecker />
    </div>
  );
}
