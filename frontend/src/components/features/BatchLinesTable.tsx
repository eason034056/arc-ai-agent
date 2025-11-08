/**
 * Batch Lines Table Component
 * Displays employee payroll lines in a table
 */

import { EmployeePayroll } from '@/lib/types/batch'
import { formatUSDC, truncateAddress } from '@/lib/utils/format'
import Badge from '@/components/ui/Badge'
import Link from 'next/link'

interface BatchLinesTableProps {
  employees: EmployeePayroll[]
  isLoading?: boolean
}

export function BatchLinesTable({ employees, isLoading }: BatchLinesTableProps) {
  if (isLoading) {
    return (
      <div className="bg-primary-800 rounded-xl shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-primary-700 rounded w-1/4"></div>
          <div className="h-32 bg-primary-700 rounded"></div>
        </div>
      </div>
    )
  }

  if (employees.length === 0) {
    return (
      <div className="bg-primary-800 rounded-xl shadow-lg p-6">
        <p className="text-gray-400 text-center py-8">No employee records found</p>
      </div>
    )
  }

  return (
    <div className="bg-primary-800 rounded-xl shadow-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-primary-700">
        <h2 className="text-lg font-semibold text-white">Employee Payroll Lines</h2>
        <p className="text-sm text-gray-400 mt-1">{employees.length} employees</p>
      </div>
      <div className="overflow-x-auto px-6">
        <table className="min-w-full">
          <thead className="bg-primary-750">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Employee ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Wallet Address
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Anomaly
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Transaction
              </th>
            </tr>
          </thead>
          <tbody className="bg-primary-800 divide-y divide-white/[0.11]">
            {employees.map((employee, index) => (
              <tr 
                key={employee.employee_id} 
                className={`hover:bg-primary-750 transition-colors ${
                  index < employees.length - 1 ? 'border-b border-white/[0.11]' : ''
                }`}
              >
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-white">
                    {employee.employee_id}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-300">
                    {employee.employee_name || 'N/A'}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-300 font-mono">
                    {truncateAddress(employee.wallet_address)}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-white font-medium">
                    {formatUSDC(employee.amount, 2)} USDC
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <Badge status={employee.status} />
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {employee.is_anomaly ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                      ⚠️ {employee.anomaly_reason || 'Anomaly'}
                    </span>
                  ) : (
                    <span className="text-gray-500 text-sm">—</span>
                  )}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {employee.transaction_hash ? (
                    <Link
                      href={`https://explorer.arc.network/tx/${employee.transaction_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-400 hover:text-primary-300 text-sm font-mono"
                    >
                      {truncateHash(employee.transaction_hash)}
                    </Link>
                  ) : (
                    <span className="text-gray-500 text-sm">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function truncateHash(hash: string, chars: number = 8): string {
  if (hash.length <= chars * 2) {
    return hash
  }
  return `${hash.slice(0, chars)}...${hash.slice(-chars)}`
}

