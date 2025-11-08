// app/page.tsx
'use client'

import { useBatchStats, useCurrentMonthBatches } from '@/hooks/useBatches'
import { useTriggerCurrentMonthBatch } from '@/hooks/useTrigger'
import { StatsCard } from '@/components/features/StatsCard'
import { Loading } from '@/components/ui/Loading'
import { formatUSDC, formatPercentage } from '@/lib/utils/format'
import Badge from '@/components/ui/Badge'
import { Batch } from '@/lib/types/batch'
import Link from 'next/link'
import { useState } from 'react'
import dynamic from 'next/dynamic'

const BatchTrendsCard = dynamic(() => import('@/components/batches/BatchTrendsCard'), { ssr: false })

export default function Home() {
  const { data: statsData, isLoading: statsLoading, error: statsError } = useBatchStats()
  const { data: currentMonthData, isLoading: currentMonthLoading } = useCurrentMonthBatches()
  const triggerBatch = useTriggerCurrentMonthBatch()
  const [showSuccess, setShowSuccess] = useState(false)

  const stats = statsData?.stats
  const currentMonthBatches = currentMonthData?.batches || []

  const handleTriggerBatch = async () => {
    try {
      const result = await triggerBatch.mutateAsync()
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 3000)
    } catch (error) {
      console.error('Failed to trigger batch:', error)
    }
  }

  if (statsLoading) {
    return <Loading fullScreen text="Loading dashboard..." />
  }

  if (statsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-primary-900 mb-2">
            Failed to load dashboard
          </h2>
          <p className="text-gray-400">
            {statsError instanceof Error ? statsError.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Header */}
      <div className="flex-shrink-0 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6 px-4 sm:px-0">
        <div className="min-w-0">
          <h1 className="text-2xl sm:text-3xl font-bold text-primary-900 truncate">
            Arc Payroll Management System
          </h1>
          <p className="mt-1 text-sm text-gray-600">Overview</p>
        </div>
        <button 
          onClick={handleTriggerBatch}
          disabled={triggerBatch.isPending}
          className="flex-shrink-0 bg-primary-600 hover:bg-primary-50 disabled:bg-primary-700 disabled:opacity-50 text-primary-50 hover:text-primary-900 px-4 sm:px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 text-sm sm:text-base whitespace-nowrap"
        >
          {triggerBatch.isPending && (
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          {triggerBatch.isPending ? 'Triggering...' : 'Trigger Batch'}
        </button>
      </div>

      {/* Main Content - 使用彈性佈局而非固定 grid */}
      <div className="flex-1 flex flex-col gap-4 sm:gap-6 min-h-0 px-4 sm:px-0">
        
        {/* Top Section - Statistics and Current Month Batches */}
        <div className="flex flex-col lg:flex-row gap-3 sm:gap-4 flex-shrink min-h-0">
          
          {/* Statistics Cards - 響應式 grid */}
          <div className="w-full lg:w-5/12 xl:w-5/12 grid grid-cols-2 gap-2 sm:gap-2 lg:gap-3 auto-rows-fr">
            <StatsCard
              title="This Month"
              value={stats?.this_month_batches || 0}
              subtitle={`${stats?.completed_batches || 0} completed`}
              color="blue"
              isLoading={statsLoading}
            />
            <StatsCard
              title="Total Distributed"
              value={formatUSDC(stats?.total_distributed || 0, 0)}
              subtitle="USDC"
              color="green"
              isLoading={statsLoading}
            />
            <StatsCard
              title="Success Rate"
              value={formatPercentage(stats?.success_rate || 0)}
              subtitle={`${stats?.total_batches || 0} total batches`}
              color="purple"
              isLoading={statsLoading}
            />
            <StatsCard
              title="Anomalies"
              value={stats?.total_anomalies || 0}
              subtitle="Needs review"
              color="orange"
              isLoading={statsLoading}
            />
          </div>

          {/* Current Month Batches - 自适应高度 */}
          <div className="w-full lg:w-7/12 xl:w-7/12 bg-primary-50 border border-primary-100 rounded-xl shadow-lg overflow-hidden flex flex-col min-h-0 flex-1">
            <div className="px-3 sm:px-4 py-2 sm:py-2.5 flex-shrink-0">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-sm sm:text-base lg:text-lg font-bold text-primary-900 truncate">
                  Current Month Batches
                </h2>
                {currentMonthBatches.length > 0 && (
                  <Link 
                    href="/batches"
                    className="text-xs sm:text-sm text-primary-600 hover:text-primary-200 font-medium transition-colors whitespace-nowrap"
                  >
                    View All →
                  </Link>
                )}
              </div>
            </div>
            {/* Current Month Batches */}
            <div className="flex-1 min-h-0 px-3 sm:px-4 pb-2 sm:pb-3">
              {currentMonthLoading ? (
                <Loading text="Loading batches..." />
              ) : currentMonthBatches.length === 0 ? (
                <div className="text-center py-8 h-full flex flex-col items-center justify-center">
                  <div className="w-12 h-12 sm:w-16 sm:h-16 bg-primary-700/50 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 sm:w-8 sm:h-8 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-base sm:text-lg font-semibold text-primary-900 mb-2">No batches found</h3>
                  <p className="text-xs sm:text-sm text-gray-400 mb-4">
                    Trigger a new batch to get started
                  </p>
                  <button 
                    onClick={handleTriggerBatch}
                    disabled={triggerBatch.isPending}
                    className="!bg-primary-700 hover:!bg-primary-700 disabled:!bg-primary-700 disabled:opacity-50 text-gray-900 px-4 sm:px-6 py-2 rounded-lg font-medium text-xs sm:text-sm transition-colors flex items-center gap-2"
                  >
                    {triggerBatch.isPending && (
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {triggerBatch.isPending ? 'Triggering...' : 'Trigger First Batch'}
                  </button>
                </div>
              ) : (
                <div className="space-y-2 sm:space-y-3 h-full flex flex-col">
                  {currentMonthBatches.map((batch: Batch) => (
                    <BatchCard key={batch.batch_id} batch={batch} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Trends - 佔據剩餘空間 */}
        <div className="flex-1 bg-primary-50 border border-primary-100 rounded-xl shadow-lg overflow-hidden flex flex-col min-h-0">
          <div className="flex-1 overflow-hidden px-3 sm:px-4 lg:px-6 py-3 sm:py-4 lg:py-6 min-h-0">
            <BatchTrendsCard />
          </div>
        </div>
      </div>

      {/* Success Message */}
      {showSuccess && triggerBatch.data && (
        <div className="mx-4 sm:mx-0 mt-4 bg-green-900/20 border border-green-700/50 rounded-lg p-4">
          <p className="text-sm text-green-300">
            ✅ {triggerBatch.data.message || 'Batch triggered successfully!'}
          </p>
        </div>
      )}

      {/* Error Message */}
      {triggerBatch.isError && (
        <div className="mx-4 sm:mx-0 mt-4 bg-red-900/20 border border-red-700/50 rounded-lg p-4">
          <p className="text-sm text-red-300">
            ❌ Failed to trigger batch: {triggerBatch.error instanceof Error ? triggerBatch.error.message : 'Unknown error'}
          </p>
        </div>
      )}
    </div>
  )
}

function BatchCard({ batch }: { batch: Batch }) {
  const successCount = batch.success_count || batch.metadata?.success_count || 0
  const totalEmployees = batch.total_employees || batch.line_count || 0
  const amount = typeof batch.total_amount === 'string' ? parseFloat(batch.total_amount) : batch.total_amount
  
  return (
    <Link href={`/batches/${batch.batch_id}`}>
      <div className="bg-white/[0.05] border border-primary-100 border-l-4 border-l-primary-600 rounded-xl p-3 sm:p-4 lg:p-6 hover:bg-primary-600/[0.15] transition-all cursor-pointer group">
        <div className="flex items-start justify-between mb-3 sm:mb-4 lg:mb-5 gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 sm:gap-3 mb-2 flex-wrap">
              <h4 className="text-base sm:text-lg font-semibold text-primary-800 group-hover:text-primary-600 transition-colors truncate">
                {batch.batch_id}
              </h4>
              <Badge status={batch.status} />
            </div>
            <p className="text-xs sm:text-sm text-gray-500">{batch.month}</p>
          </div>
          <svg className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500 group-hover:text-primary-400 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
        
        <div className="grid grid-cols-3 gap-2 sm:gap-3 lg:gap-6">
          <div className="min-w-0">
            <p className="text-gray-500 text-xs sm:text-sm mb-1 sm:mb-2 truncate">Employees</p>
            <p className="text-sm sm:text-base lg:text-xl font-semibold text-primary-900 truncate">{totalEmployees}</p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-xs sm:text-sm mb-1 sm:mb-2 truncate">Amount</p>
            <p className="text-sm sm:text-base lg:text-xl font-semibold text-primary-900 truncate">
              {formatUSDC(amount, 0)} <span className="text-xs sm:text-sm lg:text-base">USDC</span>
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-gray-500 text-xs sm:text-sm mb-1 sm:mb-2 truncate">Anomalies</p>
            <p className="text-sm sm:text-base lg:text-xl font-semibold text-orange-400 truncate">{batch.anomaly_count}</p>
          </div>
        </div>
        
        {successCount > 0 && (
          <div className="mt-3 sm:mt-4 lg:mt-5 pt-3 sm:pt-4 lg:pt-5 border-t border-white/[0.1]">
            <div className="flex items-center justify-between gap-2">
              <span className="text-gray-400 text-xs sm:text-base truncate">Success Rate</span>
              <span className="text-green-400 font-semibold text-xs sm:text-base whitespace-nowrap">
                {successCount}/{totalEmployees}
              </span>
            </div>
          </div>
        )}
      </div>
    </Link>
  )
}