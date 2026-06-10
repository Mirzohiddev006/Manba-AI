import type { Source } from '@/entities/source';

export interface RefList {
  id: number; title: string; grouping_mode: string; sort_mode: string;
  items_count: number; updated_at: string | null;
}

export interface ListItem { id: number; position: number; group_no: number; source: Source }

export interface RefListDetail extends RefList { items: ListItem[] }
