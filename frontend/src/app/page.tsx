/**
 * Home Page - Dashboard
 * Dashboard overview page with real data
 * 
 * Displays:
 * - Current month batch status
 * - Anomaly ratio
 * - USDC cost
 * - Success rate
 */

'use client'

import { useBatchStats, useCurrentMonthBatches } from '@/hooks/useBatches'
import { StatsCard } from '@/components/features/StatsCard'
import { Loading } from '@/components/ui/Loading'
import { formatUSDC, formatPercentage } from '@/lib/utils/format'
import Badge from '@/components/ui/Badge'
import { Batch } from '@/lib/types/batch'
import { MockDataBanner } from '@/components/ui/MockDataIndicator'

export default function Home() {
  const { data: statsData, isLoading: statsLoading, error: statsError } = useBatchStats()
  const { data: currentMonthData, isLoading: currentMonthLoading } = useCurrentMonthBatches()

  const stats = statsData?.stats
  const currentMonthBatches = currentMonthData?.batches || []

  // Show loading state
  if (statsLoading) {
    return <Loading fullScreen text="Loading dashboard..." />
  }

  // Show error state
  if (statsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Failed to load dashboard
          </h2>
          <p className="text-gray-500">
            {statsError instanceof Error ? statsError.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Mock Data Indicator */}
      <MockDataBanner />
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Arc Payroll Management System Overview
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
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

      {/* Recent Batches */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Current Month Batches
          </h3>
          
          {currentMonthLoading ? (
            <Loading text="Loading batches..." />
          ) : currentMonthBatches.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No batches found for this month</p>
              <p className="text-sm text-gray-400 mt-1">
                Trigger a new batch to get started
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {currentMonthBatches.map((batch: Batch) => (
                <BatchCard key={batch.batch_id} batch={batch} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* System Info */}
      {statsData?.message && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            ℹ️ {statsData.message}
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * Batch Card Component
 */
function BatchCard({ batch }: { batch: Batch }) {
  // Calculate success count from metadata or direct field
  const successCount = batch.success_count || batch.metadata?.success_count || 0
  const totalEmployees = batch.total_employees || batch.line_count || 0
  const amount = typeof batch.total_amount === 'string' ? parseFloat(batch.total_amount) : batch.total_amount
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="text-sm font-medium text-gray-900">
            Batch {batch.batch_id}
          </h4>
          <p className="text-xs text-gray-500">{batch.month}</p>
        </div>
        <Badge status={batch.status} />
      </div>
      
      <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
        <div>
          <p className="text-gray-500">Employees</p>
          <p className="font-medium text-gray-900">{totalEmployees}</p>
        </div>
        <div>
          <p className="text-gray-500">Amount</p>
          <p className="font-medium text-gray-900">
            {formatUSDC(amount, 0)} USDC
          </p>
        </div>
        <div>
          <p className="text-gray-500">Anomalies</p>
          <p className="font-medium text-orange-600">{batch.anomaly_count}</p>
        </div>
      </div>
      
      {successCount > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Success</span>
            <span className="text-green-600 font-medium">
              {successCount}/{totalEmployees}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
