/**
 * Home Page - Dashboard
 * Dashboard overview page
 * 
 * Displays:
 * - Current month batch status
 * - Anomaly ratio
 * - USDC cost
 * - Success rate
 */

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Arc Payroll Management System Overview
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="This Month"
          value="2"
          subtitle="1 completed"
          color="blue"
        />
        <StatCard
          title="Total Distributed"
          value="45,000"
          subtitle="USDC"
          color="green"
        />
        <StatCard
          title="Success Rate"
          value="98.5%"
          subtitle="147/149 successful"
          color="purple"
        />
        <StatCard
          title="Anomalies"
          value="3"
          subtitle="Needs review"
          color="orange"
        />
      </div>

      {/* Recent Batches */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Recent Batches
          </h3>
          <div className="text-sm text-gray-500">
            Coming soon: Recent batch list...
          </div>
        </div>
      </div>
    </div>
  )
}

// Statistics Card Component
function StatCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string
  value: string
  subtitle: string
  color: 'blue' | 'green' | 'purple' | 'orange'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    orange: 'bg-orange-50 text-orange-700',
  }

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
        <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
        <dd className={`mt-1 text-sm ${colorClasses[color]} inline-block px-2 py-1 rounded`}>
          {subtitle}
        </dd>
      </div>
    </div>
  )
}
