"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Users,
  Server,
  CreditCard,
  Ticket,
  Gift,
  Settings,
  BarChart3,
  Radio,
} from 'lucide-react'

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'Пользователи',
    href: '/users',
    icon: Users,
  },
  {
    name: 'Серверы',
    href: '/servers',
    icon: Server,
  },
  {
    name: 'Подписки',
    href: '/subscriptions',
    icon: CreditCard,
  },
  {
    name: 'Платежи',
    href: '/payments',
    icon: CreditCard,
  },
  {
    name: 'Промокоды',
    href: '/promo-codes',
    icon: Ticket,
  },
  {
    name: 'Рефералы',
    href: '/referrals',
    icon: Gift,
  },
  {
    name: 'Статистика',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'Рассылка',
    href: '/broadcast',
    icon: Radio,
  },
  {
    name: 'Настройки',
    href: '/settings',
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden lg:flex lg:flex-col w-64 border-r border-white/5 bg-[#0A0A0A]">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-white/5">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00FF9F] to-[#00D4FF] flex items-center justify-center">
            <span className="text-black font-bold text-lg">G</span>
          </div>
          <span className="text-xl font-bold gradient-text">
            GHETTO VPN
          </span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                isActive
                  ? 'bg-[#00FF9F]/10 text-[#00FF9F] neon-glow'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="glass-dark rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-2 h-2 rounded-full bg-[#00FF9F] animate-pulse" />
            <span className="text-xs font-medium text-gray-400">System Status</span>
          </div>
          <p className="text-xs text-gray-500">All systems operational</p>
        </div>
      </div>
    </aside>
  )
}
