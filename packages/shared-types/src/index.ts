/**
 * API kontraktlari. To'liq turlar OpenAPI dan generatsiya qilinadi:
 *   pnpm --filter @manba/shared-types generate
 * (backend lokalda ishlab turganda — http://localhost:8000/openapi.json)
 */
export type SourceType =
  | 'book' | 'book_many' | 'journal_article' | 'conference' | 'dissertation'
  | 'abstract' | 'legal' | 'web' | 'foreign_article';

export interface Person { surname: string; initials: string }
