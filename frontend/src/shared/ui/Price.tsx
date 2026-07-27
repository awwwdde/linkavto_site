import { cn } from '@/shared/lib/cn'
import { formatPrice } from '@/shared/lib/format'

export interface PriceProps {
  /** Копейки. */
  value: number
  oldValue?: number | null
  currency?: string
  size?: 'sm' | 'md' | 'lg'
  /** На тёмной карточке — светлый тон зачёркнутой цены (§3.4, контраст §13). */
  tone?: 'light' | 'dark'
  className?: string
}

const SIZES = {
  sm: 'text-base',
  md: 'text-md',
  lg: 'text-xl',
} as const

export function Price({ value, oldValue, currency, size = 'md', tone = 'light', className }: PriceProps) {
  return (
    <span className={cn('inline-flex items-baseline gap-2 tabular-nums', className)}>
      <span className={cn('font-semibold', SIZES[size])}>{formatPrice(value, currency)}</span>
      {oldValue && oldValue > value ? (
        <s className={cn('text-sm', tone === 'dark' ? 'text-ink-ghost-dark' : 'text-ink-muted')}>
          {formatPrice(oldValue, currency)}
        </s>
      ) : null}
    </span>
  )
}

/**
 * §6: сигнатурный элемент карточки — цена в аутлайн-пилюле, моноширинная,
 * tabular-nums; зачёркнутая старая цена рядом мелким (§3.1).
 * На тёмной карточке (`tone="dark"`) — светлая обводка.
 */
export function PricePill({
  value,
  oldValue,
  currency,
  tone = 'light',
  className,
}: Omit<PriceProps, 'size'> & { tone?: 'light' | 'dark' }) {
  return (
    <span className={cn('inline-flex items-baseline gap-2', className)}>
      <span
        className={cn(
          'inline-flex items-center rounded-pill border px-3.5 py-1.5 font-mono text-base font-medium tabular-nums',
          tone === 'dark' ? 'border-white/25 text-white' : 'border-line text-ink',
        )}
      >
        {formatPrice(value, currency)}
      </span>
      {oldValue && oldValue > value ? (
        <s
          className={cn(
            'font-mono text-xs tabular-nums',
            tone === 'dark' ? 'text-ink-ghost-dark' : 'text-ink-ghost',
          )}
        >
          {formatPrice(oldValue, currency)}
        </s>
      ) : null}
    </span>
  )
}
