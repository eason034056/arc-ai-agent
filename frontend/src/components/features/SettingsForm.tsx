/**
 * Settings Form Component
 * Form for configuring system settings
 */

'use client'

import { useState } from 'react'

interface SettingsFormProps {
  initialValues?: {
    rpcUrl?: string
    contractAddress?: string
    gasLimit?: number
    gasPrice?: number
  }
  onSubmit?: (values: any) => Promise<void>
}

export function SettingsForm({ initialValues, onSubmit }: SettingsFormProps) {
  const [formData, setFormData] = useState({
    rpcUrl: initialValues?.rpcUrl || '',
    contractAddress: initialValues?.contractAddress || '',
    gasLimit: initialValues?.gasLimit || 500000,
    gasPrice: initialValues?.gasPrice || 20,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!onSubmit) return

    try {
      setIsSubmitting(true)
      await onSubmit(formData)
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-primary-800 rounded-xl shadow-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Blockchain Configuration</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              RPC URL
            </label>
            <input
              type="text"
              value={formData.rpcUrl}
              onChange={(e) => setFormData({ ...formData, rpcUrl: e.target.value })}
              className="w-full rounded-lg border border-primary-600 bg-primary-700 text-white px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              placeholder="https://rpc.arc.network"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Contract Address
            </label>
            <input
              type="text"
              value={formData.contractAddress}
              onChange={(e) => setFormData({ ...formData, contractAddress: e.target.value })}
              className="w-full rounded-lg border border-primary-600 bg-primary-700 text-white px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none font-mono"
              placeholder="0x..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Gas Limit
              </label>
              <input
                type="number"
                value={formData.gasLimit}
                onChange={(e) => setFormData({ ...formData, gasLimit: parseInt(e.target.value) || 0 })}
                className="w-full rounded-lg border border-primary-600 bg-primary-700 text-white px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Gas Price (Gwei)
              </label>
              <input
                type="number"
                value={formData.gasPrice}
                onChange={(e) => setFormData({ ...formData, gasPrice: parseInt(e.target.value) || 0 })}
                className="w-full rounded-lg border border-primary-600 bg-primary-700 text-white px-3 py-2 shadow-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          {showSuccess && (
            <p className="text-green-400 text-sm">✅ Settings saved successfully!</p>
          )}
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
        >
          {isSubmitting ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </form>
  )
}

