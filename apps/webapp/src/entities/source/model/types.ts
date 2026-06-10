export type SourceType =
  | 'book' | 'book_many' | 'journal_article' | 'conference' | 'dissertation'
  | 'abstract' | 'legal' | 'web' | 'foreign_article';

export interface Person { surname: string; initials: string }

export interface SourceFields {
  authors: Person[];
  title: string; subtitle: string; city: string; publisher: string;
  year: number | null; pages_total: number | null; pages_range: string;
  journal: string; collection: string; volume: string; issue: string;
  url: string; accessed_date: string; doi: string; isbn: string;
  doc_number: string; doc_date: string; degree: string; language: string;
}

export interface Source {
  id: number;
  raw_input: string;
  source_type: SourceType;
  fields: Partial<SourceFields>;
  formatted_text: string;
  confidence: number;
  field_confidence: Record<string, number>;
  parse_method: string;
  warnings: string[];
}

export const TYPE_EMOJI: Record<SourceType, string> = {
  book: '📕', book_many: '📗', journal_article: '📄', conference: '📑',
  dissertation: '🎓', abstract: '📜', legal: '🏛', web: '🌐', foreign_article: '🌍',
};

export const TYPE_NAMES: Record<SourceType, string> = {
  book: 'Kitob/monografiya', book_many: 'Kitob (4+ muallif)',
  journal_article: 'Jurnal maqolasi', conference: 'Konferensiya maqolasi',
  dissertation: 'Dissertatsiya', abstract: 'Avtoreferat',
  legal: 'Normativ-huquqiy hujjat', web: 'Internet resurs',
  foreign_article: 'Xorijiy maqola',
};
