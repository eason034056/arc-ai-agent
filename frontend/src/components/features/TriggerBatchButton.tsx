/**
 * Trigger Batch Button Component
 * Reusable button for triggering new payroll batches
 */

'use client'

import { useTriggerCurrentMonthBatch } from '@/hooks/useTrigger'
import { useState } from 'react'

interface TriggerBatchButtonProps {
  variant?: 'default' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  onSuccess?: () => void
  onError?: (error: Error) => void
}

export function TriggerBatchButton({
  variant = 'default',
  size = 'md',
  className = '',
  onSuccess,
  onError,
}: TriggerBatchButtonProps) {
  const triggerBatch = useTriggerCurrentMonthBatch()
  const [showSuccess, setShowSuccess] = useState(false)

  const handleClick = async () => {
    try {
      await triggerBatch.mutateAsync()
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 3000)
      onSuccess?.()
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error('Unknown error'))
    }
  }

  const sizeClasses = {
    sm: 'px-4 py-1.5 text-sm',
    md: 'px-6 py-2.5 text-base',
    lg: 'px-8 py-3 text-lg',
  }

  const variantClasses = {
    default: 'bg-primary-600 hover:bg-primary-50 text-primary-50 hover:text-gray-900',
    outline: 'border border-primary-800 text-primary-700 hover:bg-primary-700 hover:text-gray-900',
  }

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        disabled={triggerBatch.isPending}
        className={`
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          disabled:opacity-50 disabled:cursor-not-allowed
          rounded-lg font-medium transition-colors
          flex items-center gap-2
          ${className}
        `}
      >
        {triggerBatch.isPending && (
          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        {triggerBatch.isPending ? 'Triggering...' : 'Trigger New Batch'}
      </button>

      {showSuccess && triggerBatch.data && (
        <div className="absolute top-full left-0 mt-2 bg-green-900/20 border border-green-700/50 rounded-lg p-2 text-sm text-green-300 whitespace-nowrap">
          ✅ {triggerBatch.data.message || 'Batch triggered successfully!'}
        </div>
      )}

      {triggerBatch.isError && (
        <div className="absolute top-full left-0 mt-2 bg-red-900/20 border border-red-700/50 rounded-lg p-2 text-sm text-red-300 whitespace-nowrap">
          ❌ {triggerBatch.error instanceof Error ? triggerBatch.error.message : 'Failed to trigger batch'}
        </div>
      )}
    </div>
  )
}

