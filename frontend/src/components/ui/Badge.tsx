/**
 * Badge Component
 * 
 * Status badge for displaying batch status, transaction status, etc.
 */

import { getStatusColor, getStatusLabel } from '@/lib/utils/format'

interface BadgeProps {
  status: string
  label?: string
  className?: string
}

export default function Badge({ status, label, className = '' }: BadgeProps) {
  const colorClass = getStatusColor(status)
  const displayLabel = label || getStatusLabel(status)

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass} ${className}`}
    >
      {displayLabel}
    </span>
  )
}

