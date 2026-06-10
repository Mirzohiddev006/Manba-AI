import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiFetch } from '@/shared/api/client';

import type { RefList, RefListDetail } from '../model/types';

export const listKeys = {
  all: ['lists'] as const,
  detail: (id: number) => ['lists', id] as const,
};

export function useLists() {
  return useQuery({ queryKey: listKeys.all, queryFn: () => apiFetch<RefList[]>('/api/v1/lists') });
}

export function useListDetail(id: number) {
  return useQuery({
    queryKey: listKeys.detail(id),
    queryFn: () => apiFetch<RefListDetail>(`/api/v1/lists/${id}`),
    enabled: id > 0,
  });
}

export function useCreateList() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (title: string) =>
      apiFetch<RefList>('/api/v1/lists', { method: 'POST', body: JSON.stringify({ title }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: listKeys.all }),
  });
}

export function useAddToList() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ listId, sourceId }: { listId: number; sourceId: number }) =>
      apiFetch(`/api/v1/lists/${listId}/items/${sourceId}`, { method: 'POST' }),
    onSuccess: (_d, { listId }) => {
      void qc.invalidateQueries({ queryKey: listKeys.detail(listId) });
      void qc.invalidateQueries({ queryKey: listKeys.all });
    },
  });
}

export function useReorder(listId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemIds: number[]) =>
      apiFetch(`/api/v1/lists/${listId}/reorder`, {
        method: 'POST',
        body: JSON.stringify({ item_ids: itemIds }),
      }),
    onSettled: () => qc.invalidateQueries({ queryKey: listKeys.detail(listId) }),
  });
}

export function useRemoveItem(listId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: number) =>
      apiFetch(`/api/v1/lists/${listId}/items/${itemId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: listKeys.detail(listId) }),
  });
}
