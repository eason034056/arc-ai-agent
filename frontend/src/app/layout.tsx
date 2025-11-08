// app/layout.tsx
import { QueryProvider } from '@/components/providers/QueryProvider'
import { NavLinks } from '@/components/navigation/NavLinks'
import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Arc Payroll Management',
  description: 'AI-powered payroll management system on Arc Testnet',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-primary-200">
        <QueryProvider>
          <div className="flex h-screen p-4 pt-0">
            {/* Sidebar Container */}
            <div className="relative flex flex-col items-center h-full">
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 z-20">
                <div className="w-32 h-32 overflow-hidden">
                  <img 
                    src="/logo.png" 
                    alt="Arc Payroll Logo" 
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>

              {/* Sidebar - 固定寬度 20，從 logo 下方開始 */}
              <aside className="w-20 bg-primary-50 border border-primary-100 rounded-xl flex flex-col items-center py-6 space-y-8 flex-1 min-h-0 mt-[90px] mb-4">
                {/* Navigation Links */}
                <nav className="flex-1 flex flex-col items-center">
                  <NavLinks />
                </nav>

                {/* Bottom Section */}
                <div className="flex flex-col items-center space-y-4">
                  <button className="w-10 h-10 rounded-full bg-primary-600/[.20] flex items-center justify-center text-primary-900 hover:bg-primary-600/[.20] transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </button>
                </div>
              </aside>
            </div>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden bg-primary-200">
              <div className="h-full px-8 pt-2 pb-4">
                {children}
              </div>
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  )
}