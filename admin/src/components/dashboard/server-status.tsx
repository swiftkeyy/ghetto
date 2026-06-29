"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { getCountryFlag, formatNumber } from '@/lib/utils'
import { Activity, AlertCircle } from 'lucide-react'

export function ServerStatus() {
  const { data: serverStats, isLoading } = useQuery({
    queryKey: ['server-statistics'],
    queryFn: () => api.getServerStatistics(),
    refetchInterval: 15000,
  })

  if (isLoading || !serverStats) {
    return null
  }

  const topServers = serverStats.servers.slice(0, 5)

  return (
    <div className="dark-card rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-1">Статус серверов</h3>
        <p className="text-sm text-gray-400">
          {serverStats.total_servers} серверов
        </p>
      </div>

      <div className="space-y-3">
        {topServers.map((server: any) => {
          const isOnline = server.status === 'online'
          const loadColor = 
            server.load_percentage < 30 ? 'text-green-500' :
            server.load_percentage < 70 ? 'text-yellow-500' :
            'text-red-500'

          return (
            <div
              key={server.id}
              className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                <span className="text-2xl">{getCountryFlag(server.country.split('-')[0])}</span>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-sm truncate">
                      {server.city}, {server.country}
                    </p>
                    {isOnline ? (
                      <Activity className="w-3 h-3 text-green-500" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-red-500" />
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span className={loadColor}>
                      {server.load_percentage}% загрузка
                    </span>
                    <span>•</span>
                    <span>{server.current_users} пользователей</span>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <p className="text-xs text-gray-500 uppercase tracking-wider">
                  {server.protocol}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-green-500">
            {serverStats.total_servers}
          </p>
          <p className="text-xs text-gray-500">Всего</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-[#00FF9F]">
            {serverStats.servers.filter((s: any) => s.status === 'online').length}
          </p>
          <p className="text-xs text-gray-500">Онлайн</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-400">
            {formatNumber(serverStats.servers.reduce((sum: number, s: any) => sum + s.current_users, 0))}
          </p>
          <p className="text-xs text-gray-500">Подключений</p>
        </div>
      </div>
    </div>
  )
}
