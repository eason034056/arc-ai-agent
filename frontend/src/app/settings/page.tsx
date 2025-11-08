/**
 * Settings Page
 * System configuration and settings
 */

'use client'

import { SettingsForm } from '@/components/features/SettingsForm'

export default function SettingsPage() {
  const handleSubmit = async (values: any) => {
    // TODO: Implement API call to save settings
    console.log('Saving settings:', values)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-400">
          Configure system parameters and blockchain settings
        </p>
      </div>

      {/* Settings Form */}
      <SettingsForm onSubmit={handleSubmit} />
    </div>
  )
}

