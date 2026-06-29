"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { formatRelativeTime, getStatusBadgeColor } from '@/lib/utils'
import { Activity, User, CreditCard, Server } from 'lucide-react'

export function RecentActivity() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 10000,
  })

  // Mock recent activity data - в продакшене это будет отдельный endpoint
  const activities = [
    {
      id: 1,
      type: 'user',
      title: 'Новый пользователь',
      description: '@john_doe зарегистрировался',
      time: new Date(Date.now() - 5 * 60 * 1000),
      icon: User,
      color: 'text-blue-500',
    },
    {
      id: 2,
      type: 'payment',
      title: 'Новый платёж',
      description: 'Пользователь #12345 оплатил $9.99',
      time: new Date(Date.now() - 15 * 60 * 1000),
      icon: CreditCard,
      color: 'text-green-500',
    },
    {
      id: 3,
      type: 'server',
      title: 'Сервер подключён',
      description: 'DE-FR вернулся в онлайн',
      time: new Date(Date.now() - 30 * 60 * 1000),
      icon: Server,
      color: 'text-purple-500',
    },
    {
      id: 4,
      type: 'activity',
      title: 'Высокая активность',
      description: '50+ активных подключений',
      time: new Date(Date.now() - 45 * 60 * 1000),
      icon: Activity,
      color: 'text-[#00FF9F]',
    },
    {
      id: 5,
      type: 'user',
      title: 'Новый пользователь',
      description: '@alice_smith зарегистрировалась',
      time: new Date(Date.now() - 60 * 60 * 1000),
      icon: User,
      color: 'text-blue-500',
    },
  ]

  return (
    <div className="dark-card rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-1">Последняя активность</h3>
        <p className="text-sm text-gray-400">В реальном времени</p>
      </div>

      <div className="space-y-4">
        {activities.map((activity) => {
          const Icon = activity.icon

          return (
            <div
              key={activity.id}
              className="flex items-start gap-4 pb-4 border-b border-white/5 last:border-0 last:pb-0"
            >
              <div className={`w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 ${activity.color}`}>
                <Icon className="w-5 h-5" />
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm mb-1">{activity.title}</p>
                <p className="text-sm text-gray-400 truncate">{activity.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatRelativeTime(activity.time)}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
