import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'
import { formatPlural } from '@/shared/lib/format'
import type { VehicleTypeMeta } from '@/shared/lib/vehicle-types'
import { IconGarage } from '@/shared/ui/Icon'

/** §3.1: иконка + подложка 10% цвета транспорта — навигационная айдентика. */
export function CategoryTile({
  to,
  name,
  productsCount,
  meta,
  className,
}: {
  to: string
  name: string
  productsCount: number
  meta: VehicleTypeMeta | null
  className?: string
}) {
  return (
    <Link
      to={to}
      className={cn(
        'flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float',
        'transition-[transform,box-shadow] duration-[--duration-base] hover:shadow-lift',
        className,
      )}
    >
      <span className={cn('flex h-12 w-12 items-center justify-center rounded-control', meta?.tile ?? 'bg-paper')}>
        <IconGarage width={24} height={24} className={meta?.text ?? 'text-ink-muted'} />
      </span>
      <span className="flex flex-col gap-1">
        <span className="text-md font-semibold">{name}</span>
        <span className="text-sm text-ink-muted tabular-nums">
          {formatPlural(productsCount, { one: 'товар', few: 'товара', many: 'товаров' })}
        </span>
      </span>
    </Link>
  )
}
