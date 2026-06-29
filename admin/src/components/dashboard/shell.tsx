"use client"

import { ReactNode } from 'react'
import { Sidebar } from '@/components/sidebar'
import { Header } from '@/components/header'

interface DashboardShellProps {
  children: ReactNode
}

export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto scrollbar-thin">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
