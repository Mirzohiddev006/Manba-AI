import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiFetch } from '@/shared/api/client';

import type { Source } from '../model/types';

export function useParseMutation() {
  return useMutation({
    mutationFn: (text: string) =>
      apiFetch<{ sources: Source[] }>('/api/v1/sources/parse', {
        method: 'POST',
        body: JSON.stringify({ text }),
      }),
  });
}

export function useSource(id: number) {
  return useQuery({
    queryKey: ['source', id],
    queryFn: () => apiFetch<Source>(`/api/v1/sources/${id}`),
    enabled: id > 0,
  });
}

export function usePatchSource(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: { fields?: Record<string, unknown>; source_type?: string }) =>
      apiFetch<Source>(`/api/v1/sources/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(patch),
      }),
    onSuccess: (data) => qc.setQueryData(['source', id], data),
  });
}
