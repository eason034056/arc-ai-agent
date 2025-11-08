'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function NavLinks() {
  const pathname = usePathname()

  const navItems = [
    { href: '/', label: 'Overview', icon: '/overview.png', iconActive: '/overview-active.png' },
    { href: '/batches', label: 'Batches', icon: '/batches.png', iconActive: '/batches-active.png' },
    { href: '/settings', label: 'Settings', icon: '/settings.png', iconActive: '/settings-active.png' },
  ]

  return (
    <div className="flex flex-col space-y-3">
      {navItems.map((item) => {
        const isActive = pathname === item.href
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`text-white px-2 py-2 rounded-full text-sm font-medium transition-colors flex items-center justify-center ${
              isActive
                ? 'bg-primary-600/[.20]'
                : 'bg-transparent hover:bg-primary-600/[.20]'
            }`}
          >
            <img 
              src={isActive ? item.iconActive : item.icon} 
              alt={item.label} 
              className="w-5 h-5 object-contain" 
            />
          </Link>
        )
      })}
    </div>
  )
}