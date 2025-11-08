/**
 * Transactions Table Component
 * Displays blockchain transactions for a batch
 */

import { Transaction } from '@/lib/types/batch'
import { formatUSDC, truncateHash } from '@/lib/utils/format'
import Badge from '@/components/ui/Badge'
import Link from 'next/link'

interface TransactionsTableProps {
  transactions: Transaction[]
  isLoading?: boolean
}

export function TransactionsTable({ transactions, isLoading }: TransactionsTableProps) {
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

  if (transactions.length === 0) {
    return (
      <div className="bg-primary-800 rounded-xl shadow-lg p-6">
        <p className="text-gray-400 text-center py-8">No transactions found</p>
      </div>
    )
  }

  return (
    <div className="bg-primary-800 rounded-xl shadow-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-primary-700">
        <h2 className="text-lg font-semibold text-white">Blockchain Transactions</h2>
        <p className="text-sm text-gray-400 mt-1">{transactions.length} transactions</p>
      </div>
      <div className="overflow-x-auto px-6">
        <table className="min-w-full">
          <thead className="bg-primary-750">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Transaction Hash
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Recipients
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Block Number
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Gas Used
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-primary-800 divide-y divide-white/[0.11]">
            {transactions.map((tx, index) => (
              <tr 
                key={tx.id} 
                className={`hover:bg-primary-750 transition-colors ${
                  index < transactions.length - 1 ? 'border-b border-white/[0.11]' : ''
                }`}
              >
                <td className="px-4 py-4 whitespace-nowrap">
                  <Link
                    href={`https://explorer.arc.network/tx/${tx.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-400 hover:text-primary-300 text-sm font-mono"
                  >
                    {truncateHash(tx.tx_hash)}
                  </Link>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <Badge status={tx.status} />
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-300">
                    {tx.recipient_count}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-white font-medium">
                    {formatUSDC(parseFloat(tx.total_amount), 2)} USDC
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-300">
                    {tx.block_number ? `#${tx.block_number.toLocaleString()}` : '—'}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-300">
                    {tx.gas_used ? tx.gas_used.toLocaleString() : '—'}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-400">
                    {new Date(tx.created_at).toLocaleDateString()}
                  </div>
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

