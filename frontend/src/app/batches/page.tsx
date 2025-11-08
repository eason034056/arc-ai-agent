// app/batches/page.tsx
'use client'

import { useState, useMemo } from 'react'
import { useBatches } from '@/hooks/useBatches'
import { Loading } from '@/components/ui/Loading'
import Badge from '@/components/ui/Badge'
import { formatUSDC, formatDate } from '@/lib/utils/format'
import { Batch, BatchStatus } from '@/lib/types/batch'
import { TriggerBatchButton } from '@/components/features/TriggerBatchButton'
import Link from 'next/link'

export default function BatchesPage() {
  const [monthFilter, setMonthFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<BatchStatus | ''>('')
  const [sortBy, setSortBy] = useState<string>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const pageSize = 10

  // 生成最近24個月的選項
  const monthOptions = useMemo(() => {
    const options = []
    const today = new Date()
    
    for (let i = 0; i < 24; i++) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const value = `${year}-${month}`
      const label = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
      
      options.push({ value, label })
    }
    
    return options
  }, [])

  const { data, isLoading, error } = useBatches({
    month: monthFilter || undefined,
    status: statusFilter || undefined,
    sort: sortBy as any,
    order: sortOrder,
    page,
    limit: pageSize,
  })

  const batches = data?.batches || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary-900">All Batches</h1>
          <p className="mt-1 text-sm text-gray-600">
            View and manage all payroll batches
          </p>
        </div>
        <div className="flex items-center gap-4">
          <TriggerBatchButton />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-primary-50 border border-primary-100 rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-primary-900 mb-2">
              Month
            </label>
            <select
              value={monthFilter}
              onChange={(e) => {
                setMonthFilter(e.target.value)
                setPage(1)
              }}
              className="w-full rounded-lg border-primary-600 bg-primary-600 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="">All Months</option>
              {monthOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-900 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as BatchStatus | '')
                setPage(1)
              }}
              className="w-full rounded-lg border-primary-600 bg-primary-600 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="">All Status</option>
              <option value={BatchStatus.DRAFT}>Draft</option>
              <option value={BatchStatus.PENDING_APPROVAL}>Pending Approval</option>
              <option value={BatchStatus.APPROVED}>Approved</option>
              <option value={BatchStatus.PROCESSING}>Processing</option>
              <option value={BatchStatus.COMPLETED}>Completed</option>
              <option value={BatchStatus.FAILED}>Failed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-900 mb-2">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value)
                setPage(1)
              }}
              className="w-full rounded-lg border-primary-600 bg-primary-600 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="created_at">Created Date</option>
              <option value="month">Month</option>
              <option value="total_amount">Amount</option>
              <option value="total_employees">Employees</option>
              <option value="anomaly_count">Anomalies</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-900 mb-2">
              Order
            </label>
            <select
              value={sortOrder}
              onChange={(e) => {
                setSortOrder(e.target.value as 'asc' | 'desc')
                setPage(1)
              }}
              className="w-full rounded-lg border-primary-600 bg-primary-600 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {/* Batches Table - 保持不變 */}
      <div className="bg-primary-50 rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="py-12">
            <Loading text="Loading batches..." />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-400">Failed to load batches</p>
            <p className="text-sm text-gray-500 mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        ) : batches.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No batches found</p>
            <p className="text-sm text-gray-500 mt-1">
              Try adjusting your filters
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto overflow-y-auto max-h-[calc(100vh-300px)] px-6">
              <table className="min-w-full">
                <thead className="bg-primary-50 sticky top-0 z-10">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Batch ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Month
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Employees
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Anomalies
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-primary-900 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-primary-50">
                  {batches.map((batch: Batch, index: number) => (
                    <tr 
                      key={batch.batch_id} 
                      className={`hover:bg-primary-600/[.30] transition-colors ${
                        index < batches.length - 1 ? 'border-b border-primary-600' : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-primary-900">
                          {batch.batch_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-primary-800">{batch.month}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge status={batch.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-primary-800">
                          {batch.total_employees || batch.line_count || 0}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-primary-800">
                          ${formatUSDC(
                            typeof batch.total_amount === 'string'
                              ? parseFloat(batch.total_amount)
                              : batch.total_amount,
                            0
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-red-400 font-medium">
                          {batch.anomaly_count}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-primary-800">
                          {formatDate(batch.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Link
                          href={`/batches/${batch.batch_id}`}
                          className="text-primary-600 hover:text-primary-800 transition-colors"
                        >
                          View Details →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-primary-600 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Showing <span className="font-medium text-primary-900">{(page - 1) * pageSize + 1}</span> to{' '}
                  <span className="font-medium text-primary-900">
                    {Math.min(page * pageSize, total)}
                  </span>{' '}
                  of <span className="font-medium text-primary-900">{total}</span> batches
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 rounded-lg border border-primary-600 text-primary-900 hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Previous
                  </button>

                  <div className="flex items-center gap-1">
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                      .filter(p => {
                        return (
                          p === 1 ||
                          p === totalPages ||
                          (p >= page - 1 && p <= page + 1)
                        )
                      })
                      .map((p, i, arr) => (
                        <div key={p} className="flex items-center gap-1">
                          {i > 0 && p - arr[i - 1] > 1 && (
                            <span className="px-2 text-gray-600">...</span>
                          )}
                          <button
                            onClick={() => setPage(p)}
                            className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                              page === p
                                ? 'bg-primary-600 text-primary-50'
                                : 'text-primary-900 hover:bg-primary-600'
                            }`}
                          >
                            {p}
                          </button>
                        </div>
                      ))}
                  </div>

                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 rounded-lg border border-primary-600 text-primary-900 hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    Next
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
