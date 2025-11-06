/**
 * Batches Hooks (Mock Version)
 * React Query hooks using mock data
 * 
 * USAGE:
 * In your components, import from this file instead of useBatches.ts
 * 
 * When backend is ready:
 * 1. Delete this file
 * 2. Update imports to use the real useBatches.ts
 */

'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBatches, getBatchById, getBatchStats } from '@/lib/api/batches.mock'
import { BatchListParams } from '@/lib/types/batch'

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
 * Hook: Get all batches with optional filters (MOCK)
 */
export const useBatches = (params?: BatchListParams) => {
  return useQuery({
    queryKey: batchKeys.list(params),
    queryFn: () => getBatches(params),
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook: Get batch by ID (MOCK)
 */
export const useBatch = (batchId: string) => {
  return useQuery({
    queryKey: batchKeys.detail(batchId),
    queryFn: () => getBatchById(batchId),
    enabled: !!batchId,
    staleTime: 30000,
  })
}

/**
 * Hook: Get batch statistics (MOCK)
 */
export const useBatchStats = () => {
  return useQuery({
    queryKey: batchKeys.stats(),
    queryFn: getBatchStats,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook: Get current month batches (MOCK)
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
