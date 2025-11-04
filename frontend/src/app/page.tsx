/**
 * Home Page - Dashboard
 * 首頁 - 儀表板總覽
 * 
 * 顯示：
 * - 當月批次狀態
 * - 異常比率
 * - USDC 成本
 * - 成功率
 */

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">儀表板</h2>
        <p className="mt-1 text-sm text-gray-500">
          Arc Payroll 薪資管理系統總覽
        </p>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="當月批次"
          value="2"
          subtitle="已完成 1 筆"
          color="blue"
        />
        <StatCard
          title="總發放金額"
          value="45,000"
          subtitle="USDC"
          color="green"
        />
        <StatCard
          title="成功率"
          value="98.5%"
          subtitle="147/149 筆成功"
          color="purple"
        />
        <StatCard
          title="異常偵測"
          value="3"
          subtitle="需要審核"
          color="orange"
        />
      </div>

      {/* 最近批次 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            最近批次
          </h3>
          <div className="text-sm text-gray-500">
            即將推出：最近批次列表...
          </div>
        </div>
      </div>
    </div>
  )
}

// 統計卡片組件
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

