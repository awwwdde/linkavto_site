import type { Review } from '@/shared/api/types'
import { formatDate } from '@/shared/lib/format'
import { t } from '@/shared/i18n'
import { RatingStars } from '@/shared/ui'

/** §10.1: блок не рендерится вовсе, если отзывов нет. */
export function ReviewList({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">{t('product.reviews')}</h2>
      <ul className="flex flex-col gap-3">
        {reviews.map((review) => (
          <li key={review.id} className="flex flex-col gap-2 rounded-card bg-surface p-4 shadow-float">
            <div className="flex items-center justify-between gap-3">
              <span className="text-base font-medium">{review.author}</span>
              <span className="text-sm text-ink-muted">{formatDate(review.created_at)}</span>
            </div>
            <RatingStars value={review.rating} />
            <p className="text-base text-ink-muted">{review.text}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
