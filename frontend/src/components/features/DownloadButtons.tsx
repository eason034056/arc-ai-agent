/**
 * Download Buttons Component
 * Buttons for downloading reports in different formats
 */

'use client'

import { useState } from 'react'
import { downloadReconcileReportCSV, triggerCSVDownload } from '@/lib/api/reports'

interface DownloadButtonsProps {
  month: string
  batchId?: string
}

export function DownloadButtons({ month, batchId }: DownloadButtonsProps) {
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownloadCSV = async () => {
    try {
      setIsDownloading(true)
      const blob = await downloadReconcileReportCSV(month)
      const filename = `reconciliation-${month}${batchId ? `-${batchId}` : ''}.csv`
      triggerCSVDownload(blob, filename)
    } catch (error) {
      console.error('Failed to download CSV:', error)
      alert('Failed to download report. Please try again.')
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleDownloadCSV}
        disabled={isDownloading}
        className="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
      >
        {isDownloading ? (
          <>
            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Downloading...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download CSV
          </>
        )}
      </button>
    </div>
  )
}

