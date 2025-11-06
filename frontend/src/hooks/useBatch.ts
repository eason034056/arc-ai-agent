/**
 * useBatch Hook
 * 
 * React Query hook for fetching a single batch
 */

import { useQuery } from '@tanstack/react-query'
import { getBatch } from '../lib/api/batches'

export function useBatch(batchId: string | null) {
  return useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => getBatch(batchId!),
    enabled: !!batchId, // Only fetch if batchId is provided
    staleTime: 30000,
    refetchOnWindowFocus: true,
  })
}

