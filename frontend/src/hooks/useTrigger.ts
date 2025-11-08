/**
 * useTrigger Hook
 * React Query hook for triggering batch operations
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { triggerBatch, triggerCurrentMonthBatch } from '@/lib/api/admin'
import { TriggerBatchResponse } from '@/lib/types/api'

/**
 * Hook to trigger a batch for a specific month
 */
export function useTriggerBatch() {
  const queryClient = useQueryClient()

  return useMutation<TriggerBatchResponse, Error, string>({
    mutationFn: (month: string) => triggerBatch(month),
    onSuccess: () => {
      // Invalidate and refetch batch-related queries
      queryClient.invalidateQueries({ queryKey: ['batches'] })
      queryClient.invalidateQueries({ queryKey: ['batchStats'] })
      queryClient.invalidateQueries({ queryKey: ['currentMonthBatches'] })
    },
  })
}

/**
 * Hook to trigger a batch for the current month
 */
export function useTriggerCurrentMonthBatch() {
  const queryClient = useQueryClient()

  return useMutation<TriggerBatchResponse, Error, void>({
    mutationFn: () => triggerCurrentMonthBatch(),
    onSuccess: () => {
      // Invalidate and refetch batch-related queries
      queryClient.invalidateQueries({ queryKey: ['batches'] })
      queryClient.invalidateQueries({ queryKey: ['batchStats'] })
      queryClient.invalidateQueries({ queryKey: ['currentMonthBatches'] })
    },
  })
}