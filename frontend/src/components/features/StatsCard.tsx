/**
 * Stats Card Component
 * Reusable statistics card for dashboard
 */

import { ReactNode } from 'react'

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red'
  isLoading?: boolean
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'blue',
  isLoading = false,
}: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    orange: 'bg-orange-50 text-orange-700',
    red: 'bg-red-50 text-red-700',
  }

  if (isLoading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-3 py-3 sm:px-4 sm:py-3 animate-pulse">
          <div className="h-3 sm:h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-6 sm:h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 sm:h-4 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-primary-50 border border-primary-100 overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
      <div className="px-3 py-3 sm:px-4 sm:py-3">
        <div className="flex items-center justify-between mb-2 sm:mb-3">
          <dt className="text-xs sm:text-sm font-medium text-primary-800 truncate">{title}</dt>
          {icon && <div className="text-primary-900">{icon}</div>}
        </div>
        
        <dd className="mt-1 sm:mt-2 text-xl sm:text-2xl lg:text-3xl font-semibold text-primary-900">{value}</dd>
        
        {subtitle && (
          <dd className={`mt-2 sm:mt-3 text-xs ${colorClasses[color]} inline-block px-2 py-0.5 rounded`}>
            {subtitle}
          </dd>
        )}
        
        {trend && (
          <div className="mt-2 sm:mt-3 flex items-center text-xs sm:text-sm">
            <span
              className={`flex items-center ${
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {trend.isPositive ? (
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {Math.abs(trend.value)}%
            </span>
            <span className="text-primary-300 ml-1">vs last month</span>
          </div>
        )}
      </div>
    </div>
  )
}