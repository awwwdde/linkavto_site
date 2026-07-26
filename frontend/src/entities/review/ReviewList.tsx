import type { Review } from '@/shared/api/types'
import { formatDate, formatPlural } from '@/shared/lib/format'
import { t } from '@/shared/i18n'
import { RatingStars } from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'

/** §10.1: блок не рендерится вовсе, если отзывов нет. */
export function ReviewList({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <SectionHeading
        lead={t('product.reviews')}
        ghost={formatPlural(reviews.length, { one: 'отзыв', few: 'отзыва', many: 'отзывов' })}
      />
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
