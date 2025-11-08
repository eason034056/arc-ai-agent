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

const colorMap: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  rejected: 'bg-red-100 text-red-800',
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
}