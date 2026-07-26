import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'

/**
 * §3.1, §4б зона 2: плитка выбора техники. Иконка нейтральная (--color-icon),
 * без цветной подложки; название снизу. Квадратная плитка бенто.
 */
export function CategoryTile({
  to,
  name,
  icon,
  className,
}: {
  to: string
  name: string
  icon: ReactNode
  className?: string
}) {
  return (
    <Link
      to={to}
      className={cn(
        'flex aspect-square flex-col justify-between rounded-card border border-line bg-surface p-4',
        'transition-[border-color,box-shadow] duration-[--duration-base] hover:border-ink-muted hover:shadow-float',
        className,
      )}
    >
      <span className="text-icon">{icon}</span>
      <span className="text-md font-medium text-ink">{name}</span>
    </Link>
  )
}
