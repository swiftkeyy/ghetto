interface DashboardHeaderProps {
  heading: string
  text?: string
  children?: React.ReactNode
}

export function DashboardHeader({
  heading,
  text,
  children,
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between pb-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{heading}</h1>
        {text && <p className="text-gray-400">{text}</p>}
      </div>
      {children}
    </div>
  )
}
