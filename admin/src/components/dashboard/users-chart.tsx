"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export function UsersChart() {
  const { data: growthData, isLoading } = useQuery({
    queryKey: ['growth-stats', 30],
    queryFn: () => api.getGrowthStats(30),
  })

  if (isLoading || !growthData) {
    return null
  }

  const chartData = growthData.daily_stats
    .slice(-14) // Last 14 days
    .map((stat: any) => ({
      date: new Date(stat.date).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
      users: stat.new_users,
    }))

  return (
    <div className="dark-card rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-1">Новые пользователи</h3>
        <p className="text-sm text-gray-400">Последние 14 дней</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            stroke="#666"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#666"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111',
              border: '1px solid rgba(0, 255, 159, 0.2)',
              borderRadius: '8px',
              color: '#fff',
            }}
            formatter={(value: any) => [value, 'Пользователей']}
          />
          <Bar
            dataKey="users"
            fill="#00FF9F"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
