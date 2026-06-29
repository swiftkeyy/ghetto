import { Suspense } from 'react'
import { DashboardShell } from '@/components/dashboard/shell'
import { DashboardHeader } from '@/components/dashboard/header'
import { StatsCards } from '@/components/dashboard/stats-cards'
import { RevenueChart } from '@/components/dashboard/revenue-chart'
import { UsersChart } from '@/components/dashboard/users-chart'
import { RecentActivity } from '@/components/dashboard/recent-activity'
import { ServerStatus } from '@/components/dashboard/server-status'
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardPage() {
  return (
    <DashboardShell>
      <DashboardHeader
        heading="Dashboard"
        text="Обзор статистики и активности системы"
      />
      
      <div className="space-y-6">
        {/* Stats Overview */}
        <Suspense fallback={<StatsCardsSkeleton />}>
          <StatsCards />
        </Suspense>

        {/* Charts */}
        <div className="grid gap-6 md:grid-cols-2">
          <Suspense fallback={<ChartSkeleton />}>
            <RevenueChart />
          </Suspense>
          
          <Suspense fallback={<ChartSkeleton />}>
            <UsersChart />
          </Suspense>
        </div>

        {/* Activity and Servers */}
        <div className="grid gap-6 md:grid-cols-2">
          <Suspense fallback={<CardSkeleton />}>
            <RecentActivity />
          </Suspense>
          
          <Suspense fallback={<CardSkeleton />}>
            <ServerStatus />
          </Suspense>
        </div>
      </div>
    </DashboardShell>
  )
}

function StatsCardsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="dark-card rounded-lg p-6">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-32 mb-1" />
          <Skeleton className="h-3 w-20" />
        </div>
      ))}
    </div>
  )
}

function ChartSkeleton() {
  return (
    <div className="dark-card rounded-lg p-6">
      <Skeleton className="h-6 w-40 mb-4" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

function CardSkeleton() {
  return (
    <div className="dark-card rounded-lg p-6">
      <Skeleton className="h-6 w-40 mb-4" />
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    </div>
  )
}
