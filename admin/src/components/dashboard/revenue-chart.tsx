"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { formatCurrency } from '@/lib/utils'

export function RevenueChart() {
  const { data: growthData, isLoading } = useQuery({
    queryKey: ['growth-stats', 30],
    queryFn: () => api.getGrowthStats(30),
  })

  if (isLoading || !growthData) {
    return null
  }

  const chartData = growthData.daily_stats.map((stat: any) => ({
    date: new Date(stat.date).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
    revenue: stat.revenue,
  }))

  return (
    <div className="dark-card rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-1">Доход</h3>
        <p className="text-sm text-gray-400">Последние 30 дней</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00FF9F" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00FF9F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            stroke="#666"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#666"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111',
              border: '1px solid rgba(0, 255, 159, 0.2)',
              borderRadius: '8px',
              color: '#fff',
            }}
            formatter={(value: any) => [`$${value.toFixed(2)}`, 'Доход']}
          />
          <Area
            type="monotone"
            dataKey="revenue"
            stroke="#00FF9F"
            strokeWidth={2}
            fill="url(#revenueGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
