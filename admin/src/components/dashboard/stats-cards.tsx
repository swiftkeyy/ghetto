"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { formatNumber, formatCurrency, calculatePercentageChange } from '@/lib/utils'
import { Users, DollarSign, Server, Activity, TrendingUp, TrendingDown } from 'lucide-react'

export function StatsCards() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading || !stats) {
    return null
  }

  const cards = [
    {
      title: 'Всего пользователей',
      value: formatNumber(stats.users.total),
      change: stats.users.today_new,
      changeLabel: 'новых сегодня',
      icon: Users,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: 'Premium подписок',
      value: formatNumber(stats.users.premium),
      change: stats.users.premium,
      changeLabel: 'активных',
      icon: Activity,
      color: 'from-[#00FF9F] to-[#00D4FF]',
    },
    {
      title: 'Доход за месяц',
      value: formatCurrency(stats.revenue.this_month, stats.revenue.currency),
      change: stats.revenue.today,
      changeLabel: 'сегодня',
      icon: DollarSign,
      color: 'from-green-500 to-emerald-500',
    },
    {
      title: 'Онлайн серверов',
      value: `${stats.servers.online}/${stats.servers.total}`,
      change: stats.connections.active,
      changeLabel: 'активных подключений',
      icon: Server,
      color: 'from-purple-500 to-pink-500',
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon
        
        return (
          <div
            key={card.title}
            className="dark-card rounded-lg p-6 card-hover"
          >
            {/* Icon */}
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>

            {/* Content */}
            <div>
              <p className="text-sm text-gray-400 mb-1">{card.title}</p>
              <h3 className="text-3xl font-bold mb-2">{card.value}</h3>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-[#00FF9F]">+{card.change}</span>
                <span className="text-gray-500">{card.changeLabel}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
