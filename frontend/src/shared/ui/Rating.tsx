import { cn } from '@/shared/lib/cn'
import { formatPlural } from '@/shared/lib/format'
import { t } from '@/shared/i18n'
import { IconStar } from './Icon'

export interface RatingProps {
  value: number
  reviewsCount: number
  showCount?: boolean
  className?: string
}

/** §10.1: рендерится только при reviews_count > 0 — за этим следит вызывающая сторона. */
export function Rating({ value, reviewsCount, showCount = true, className }: RatingProps) {
  const rounded = Math.round(value * 10) / 10
  return (
    <span
      className={cn('inline-flex items-center gap-1.5 text-sm text-ink-muted tabular-nums', className)}
      aria-label={`${t('common.rating')} ${rounded} ${t('common.from')} 5`}
    >
      <IconStar width={16} height={16} className="fill-current text-ink" />
      <span className="font-medium text-ink">{rounded.toFixed(1)}</span>
      {showCount ? (
        <span>{formatPlural(reviewsCount, { one: 'отзыв', few: 'отзыва', many: 'отзывов' })}</span>
      ) : null}
    </span>
  )
}

export function RatingStars({ value, className }: { value: number; className?: string }) {
  return (
    <span className={cn('inline-flex gap-0.5 text-ink', className)} aria-hidden="true">
      {[1, 2, 3, 4, 5].map((star) => (
        <IconStar key={star} width={16} height={16} className={star <= Math.round(value) ? 'fill-current' : 'opacity-30'} />
      ))}
    </span>
  )
}
