/**
 * Batch Detail Page
 * Displays detailed information about a specific batch
 */

'use client'

import { useParams } from 'next/navigation'
import { useBatch } from '@/hooks/useBatch'
import { Loading } from '@/components/ui/Loading'
import { BatchDetailHeader } from '@/components/features/BatchDetailHeader'
import { BatchLinesTable } from '@/components/features/BatchLinesTable'
import { TransactionsTable } from '@/components/features/TransactionsTable'
import { DownloadButtons } from '@/components/features/DownloadButtons'
import Link from 'next/link'

export default function BatchDetailPage() {
  const params = useParams()
  const batchId = params?.batchId as string

  const { data, isLoading, error } = useBatch(batchId)

  if (isLoading) {
    return <Loading fullScreen text="Loading batch details..." />
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-white mb-2">
            Failed to load batch
          </h2>
          <p className="text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Link
            href="/batches"
            className="text-primary-400 hover:text-primary-300"
          >
            ← Back to Batches
          </Link>
        </div>
      </div>
    )
  }

  if (!data?.batch) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-white mb-2">
            Batch not found
          </h2>
          <Link
            href="/batches"
            className="text-primary-400 hover:text-primary-300"
          >
            ← Back to Batches
          </Link>
        </div>
      </div>
    )
  }

  const batch = data.batch

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link
          href="/batches"
          className="text-primary-400 hover:text-primary-300 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Batches
        </Link>
        <DownloadButtons month={batch.month} batchId={batch.batch_id} />
      </div>

      {/* Batch Header */}
      <BatchDetailHeader batch={batch} />

      {/* Employee Payroll Lines */}
      {batch.employees && batch.employees.length > 0 && (
        <BatchLinesTable employees={batch.employees} />
      )}

      {/* Transactions */}
      {batch.transactions && batch.transactions.length > 0 && (
        <TransactionsTable transactions={batch.transactions} />
      )}

      {/* Blockchain Info */}
      {batch.blockchain_info && (
        <div className="bg-primary-800 rounded-xl shadow-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Blockchain Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-400 text-sm mb-1">Network</p>
              <p className="text-white">{batch.blockchain_info.network}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Contract Address</p>
              <p className="text-white font-mono text-sm">{batch.blockchain_info.contract_address}</p>
            </div>
            {batch.blockchain_info.total_gas_used && (
              <div>
                <p className="text-gray-400 text-sm mb-1">Total Gas Used</p>
                <p className="text-white">{batch.blockchain_info.total_gas_used.toLocaleString()}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

