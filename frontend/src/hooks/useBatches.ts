/**
 * Batches Hooks
 * React Query hooks for batch operations
 */

'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBatches, getBatchById, getBatchStats } from '@/lib/api/batches'
import { BatchListParams, BatchDetail } from '@/lib/types/batch'
import { BatchDetailResponse } from '@/lib/types/api'

/**
 * Query Keys
 */
export const batchKeys = {
  all: ['batches'] as const,
  lists: () => [...batchKeys.all, 'list'] as const,
  list: (params?: BatchListParams) => [...batchKeys.lists(), params] as const,
  details: () => [...batchKeys.all, 'detail'] as const,
  detail: (id: string) => [...batchKeys.details(), id] as const,
  stats: () => [...batchKeys.all, 'stats'] as const,
}

/**
 * Hook: Get all batches with optional filters
 */
export const useBatches = (params?: BatchListParams) => {
  return useQuery({
    queryKey: batchKeys.list(params),
    queryFn: () => getBatches(params),
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook: Get batch by ID
 */
export const useBatch = (batchId: string) => {
  return useQuery<BatchDetailResponse>({
    queryKey: batchKeys.detail(batchId),
    queryFn: () => getBatchById(batchId),
    enabled: !!batchId, // Only fetch if batchId is provided
    staleTime: 30000,
  })
}

/**
 * Hook: Get batch statistics
 */
export const useBatchStats = () => {
  return useQuery({
    queryKey: batchKeys.stats(),
    queryFn: getBatchStats,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook: Get current month batches
 */
export const useCurrentMonthBatches = () => {
  const currentMonth = new Date().toISOString().slice(0, 7)
  return useBatches({ month: currentMonth })
}

/**
 * Hook: Refetch batch data
 */
export const useRefetchBatches = () => {
  const queryClient = useQueryClient()
  
  return () => {
    queryClient.invalidateQueries({ queryKey: batchKeys.all })
  }
}
