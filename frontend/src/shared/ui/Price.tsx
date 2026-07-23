import { cn } from '@/shared/lib/cn'
import { formatPrice } from '@/shared/lib/format'

export interface PriceProps {
  /** Копейки. */
  value: number
  oldValue?: number | null
  currency?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZES = {
  sm: 'text-base',
  md: 'text-md',
  lg: 'text-xl',
} as const

export function Price({ value, oldValue, currency, size = 'md', className }: PriceProps) {
  return (
    <span className={cn('inline-flex items-baseline gap-2 tabular-nums', className)}>
      <span className={cn('font-semibold', SIZES[size])}>{formatPrice(value, currency)}</span>
      {oldValue && oldValue > value ? (
        <s className="text-sm text-ink-muted">{formatPrice(oldValue, currency)}</s>
      ) : null}
    </span>
  )
}
