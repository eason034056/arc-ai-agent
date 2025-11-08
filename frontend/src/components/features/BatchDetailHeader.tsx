/**
 * Batch Detail Header Component
 * Displays batch information header with key metrics
 */

import { BatchDetail } from '@/lib/types/batch'
import Badge from '@/components/ui/Badge'
import { formatUSDC, formatDate } from '@/lib/utils/format'

interface BatchDetailHeaderProps {
  batch: BatchDetail
}

export function BatchDetailHeader({ batch }: BatchDetailHeaderProps) {
  const amount = typeof batch.total_amount === 'string' 
    ? parseFloat(batch.total_amount) 
    : batch.total_amount

  return (
    <div className="bg-primary-800 rounded-xl shadow-lg p-6 mb-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-white">{batch.batch_id}</h1>
            <Badge status={batch.status} />
          </div>
          <p className="text-gray-400 text-sm">Month: {batch.month}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-white mb-1">
            {formatUSDC(amount, 0)} USDC
          </p>
          <p className="text-gray-400 text-sm">Total Amount</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-primary-700">
        <div>
          <p className="text-gray-400 text-sm mb-1">Employees</p>
          <p className="text-xl font-semibold text-white">
            {batch.total_employees || batch.line_count || 0}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm mb-1">Success</p>
          <p className="text-xl font-semibold text-green-400">
            {batch.success_count || 0}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm mb-1">Failed</p>
          <p className="text-xl font-semibold text-red-400">
            {batch.failed_count || 0}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm mb-1">Anomalies</p>
          <p className="text-xl font-semibold text-orange-400">
            {batch.anomaly_count}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-primary-700">
        <div>
          <p className="text-gray-400 text-sm mb-1">Created</p>
          <p className="text-white">{formatDate(batch.created_at)}</p>
        </div>
        {batch.approved_at && (
          <div>
            <p className="text-gray-400 text-sm mb-1">Approved</p>
            <p className="text-white">{formatDate(batch.approved_at)}</p>
          </div>
        )}
        {batch.completed_at && (
          <div>
            <p className="text-gray-400 text-sm mb-1">Completed</p>
            <p className="text-white">{formatDate(batch.completed_at)}</p>
          </div>
        )}
      </div>

      {batch.notes && (
        <div className="mt-6 pt-6 border-t border-primary-700">
          <p className="text-gray-400 text-sm mb-1">Notes</p>
          <p className="text-white">{batch.notes}</p>
        </div>
      )}
    </div>
  )
}

