"use client"

import { useMemo, useState, useRef, useEffect } from "react"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, AreaChart, Area, BarChart, Bar } from "recharts"
import { useBatches } from "@/hooks/useBatches"
import { Batch } from "@/lib/types/batch"

/**
 * BatchTrendsCard
 * Quick, drop-in chart for visualizing batch totals across months
 * - Pulls up to 120 recent batches (adjustable) and aggregates by YYYY-MM
 * - Toggle metric: total_amount / total_employees / anomaly_count
 * - Works with your dark "primary-*" theme
 */
export default function BatchTrendsCard() {
  const [metric, setMetric] = useState<"total_amount" | "total_employees" | "anomaly_count">("total_amount")
  const [chartType, setChartType] = useState<"line" | "area" | "bar">("line")
  const [chartTypeOpen, setChartTypeOpen] = useState(false)
  const chartTypeRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (chartTypeRef.current && !chartTypeRef.current.contains(event.target as Node)) {
        setChartTypeOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Fetch more rows than the paginated table so we can build a trend
  const { data, isLoading, error } = useBatches({
    page: 1,
    limit: 120, // ~10 years if monthly
    order: "asc",
    sort: "month",
  })

  const monthly = useMemo(() => {
    const map = new Map<string, { month: string; total_amount: number; total_employees: number; anomaly_count: number }>()
    const list: Batch[] = data?.batches ?? []

    for (const b of list) {
      const key = b.month ?? (typeof b.created_at === "string" ? (b.created_at as string).slice(0, 7) : "")
      if (!key) continue
      const curr = map.get(key) ?? { month: key, total_amount: 0, total_employees: 0, anomaly_count: 0 }

      const amount = typeof b.total_amount === "string" ? parseFloat(b.total_amount) : (b.total_amount ?? 0)
      const employees = (b.total_employees ?? b.line_count ?? 0) as number
      const anomalies = (b.anomaly_count ?? 0) as number

      curr.total_amount += isFinite(amount) ? amount : 0
      curr.total_employees += isFinite(employees) ? employees : 0
      curr.anomaly_count += isFinite(anomalies) ? anomalies : 0
      map.set(key, curr)
    }

    // Sort by YYYY-MM
    return Array.from(map.values()).sort((a, b) => (a.month < b.month ? -1 : 1))
  }, [data])

  const latest = monthly.at(-1)
  const prev = monthly.length > 1 ? monthly[monthly.length - 2] : undefined
  const delta = latest && prev ? ((latest[metric] - prev[metric]) / (prev[metric] || 1)) * 100 : 0

  // Format Y-axis tick values with comma separators
  const formatYAxisTick = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  // Format Tooltip values with comma separators
  const formatTooltipValue = (value: number | string) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(numValue)) return value
    return new Intl.NumberFormat('en-US').format(numValue)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header Section */}
      <div className="flex flex-wrap items-end justify-between gap-4 mb-4 flex-shrink-0 ">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-xl font-semibold text-primary-900">Batch Trends</h2>
          </div>

          {/* Metric Selector  */}
          <div className="flex items-center gap-2">
            {(["total_amount", "total_employees", "anomaly_count"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`rounded-full border text-sm px-4 py-2 transition-colors ${
                  metric === m
                    ? "border-primary-600 bg-primary-600 text-primary-50"
                    : "border-primary-100 bg-primary-50 text-primary-900 hover:bg-primary-600 hover:text-primary-50"
                }`}
              >
                {labelOf(m)}
              </button>
            ))}
          </div>
        </div>

        {/* Chart Type Selector - 下拉框 */}
        <div className="relative" ref={chartTypeRef}>
          <button
            onClick={() => setChartTypeOpen(!chartTypeOpen)}
            className="rounded-full border border-primary-600 bg-primary-600 text-primary-50 text-sm px-4 py-2 hover:bg-primary-600 hover:text-primary-50 transition-colors flex items-center gap-2"
          >
            <span className="capitalize">{chartType}</span>
            <svg className={`w-4 h-4 transition-transform ${chartTypeOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {chartTypeOpen && (
            <div className="absolute top-full left-0 mt-2 bg-primary-800 rounded-lg border border-primary-700 shadow-lg z-10 min-w-[120px]">
              {(["line", "area", "bar"] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => {
                    setChartType(type)
                    setChartTypeOpen(false)
                  }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors first:rounded-t-lg last:rounded-b-lg capitalize ${
                    chartType === type
                      ? "bg-primary-700 text-white"
                      : "text-gray-300 hover:bg-white/[0.11] hover:text-white"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4 flex-shrink-0">
        <KpiCard label="Current Month" value={fmt(metric, latest?.[metric])} sub={latest?.month ?? "–"} />
        <KpiCard label="Previous Month" value={fmt(metric, prev?.[metric])} sub={prev?.month ?? "–"} />
        <KpiDelta label="Month Change" delta={delta} />
      </div>

      {/* Chart - Takes remaining space */}
      <div className="flex-1 min-h-0 -mb-2">
        {isLoading ? (
          <div className="h-full flex items-center justify-center text-gray-400">Loading chart…</div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-red-400">Failed to load trend</div>
        ) : monthly.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-400">No data</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === "line" ? (
              <LineChart data={monthly} margin={{ left: 8, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="month" tick={{ fill: "#9CA3AF", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis 
                  tick={{ fill: "#9CA3AF", fontSize: 12 }} 
                  axisLine={false} 
                  tickLine={false}
                  tickFormatter={formatYAxisTick}
                />
                <Tooltip 
                  contentStyle={{ 
                    background: "rgba(255, 255, 255)", 
                    border: "1px solid #E6E9EE", 
                    borderRadius: 12,
                    padding: 12
                  }} 
                  labelStyle={{ color: "#1B1B1B", fontWeight: 600 }}
                  itemStyle={{ color: "#1B1B1B" }}
                  formatter={(value: number | string) => formatTooltipValue(value)}
                />
                <Legend wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }} />
                <Line 
                  type="monotone" 
                  dataKey={metric} 
                  stroke="#00B3FF" 
                  strokeWidth={3} 
                  dot={{ fill: "#00B3FF", r: 4 }}
                  activeDot={{ r: 6 }}
                  name={labelOf(metric)} 
                />
              </LineChart>
            ) : chartType === "area" ? (
              <AreaChart data={monthly} margin={{ left: 8, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="month" tick={{ fill: "#9CA3AF", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis 
                  tick={{ fill: "#9CA3AF", fontSize: 12 }} 
                  axisLine={false} 
                  tickLine={false}
                  tickFormatter={formatYAxisTick}
                />
                <Tooltip 
                  contentStyle={{ 
                    background: "rgba(255, 255, 255)", 
                    border: "1px solid #E6E9EE", 
                    borderRadius: 12,
                    padding: 12
                  }} 
                  labelStyle={{ color: "#1B1B1B", fontWeight: 600 }}
                  itemStyle={{ color: "#1B1B1B" }}
                  formatter={(value: number | string) => formatTooltipValue(value)}
                />
                <Legend wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }} />
                <Area 
                  type="monotone" 
                  dataKey={metric} 
                  stroke="#00B3FF" 
                  strokeWidth={2}
                  fill="#00B3FF" 
                  fillOpacity={0.3} 
                  name={labelOf(metric)} 
                />
              </AreaChart>
            ) : (
              <BarChart data={monthly} margin={{ left: 8, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="month" tick={{ fill: "#9CA3AF", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis 
                  tick={{ fill: "#9CA3AF", fontSize: 12 }} 
                  axisLine={false} 
                  tickLine={false}
                  tickFormatter={formatYAxisTick}
                />
                <Tooltip 
                  contentStyle={{ 
                    background: "rgba(255, 255, 255)", 
                    border: "1px solid #E6E9EE", 
                    borderRadius: 12,
                    padding: 12
                  }} 
                  labelStyle={{ color: "#E6E9EE", fontWeight: 600 }}
                  itemStyle={{ color: "#E6E9EE" }}
                  formatter={(value: number | string) => formatTooltipValue(value)}
                />
                <Legend wrapperStyle={{ color: "#9CA3AF", fontSize: 12 }} />
                <Bar 
                  dataKey={metric} 
                  name={labelOf(metric)} 
                  fill="#00B3FF"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function fmt(metric: string, v?: number) {
  if (v == null) return "–"
  if (metric === "total_amount") return new Intl.NumberFormat("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v)
  return new Intl.NumberFormat("en-US").format(v)
}

function labelOf(metric: "total_amount" | "total_employees" | "anomaly_count") {
  switch (metric) {
    case "total_amount":
      return "Amount (USDC)"
    case "total_employees":
      return "Employees"
    case "anomaly_count":
      return "Anomalies"
  }
}

function KpiCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-primary-50 border border-primary-100 border-l-4 border-l-primary-600 rounded-lg p-4 transition-colors">
      <div className="text-xs text-primary-800 uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold text-primary-900 mt-2">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  )
}

function KpiDelta({ label, delta }: { label: string; delta: number }) {
  const isUp = delta >= 0
  const sign = isUp ? "+" : ""
  return (
    <div className="bg-primary-50 border border-primary-100 border-l-4 border-l-primary-600 rounded-lg p-4 transition-colors">
      <div className="text-xs text-primary-800 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-2 flex items-center gap-2 ${isUp ? "text-green-400" : "text-red-400"}`}>
        {isUp ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
          </svg>
        )}
        {sign}{delta.toFixed(1)}%
      </div>
      <div className="text-xs text-gray-500 mt-1">vs previous month</div>
    </div>
  )
}