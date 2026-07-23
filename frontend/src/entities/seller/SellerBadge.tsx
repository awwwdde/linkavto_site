import { Link } from 'react-router'
import type { SellerBrief } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { Rating } from '@/shared/ui'

export function SellerBadge({ seller, className }: { seller: SellerBrief; className?: string }) {
  return (
    <span className={cn('flex flex-col gap-0.5', className)}>
      <Link to={`/seller/${seller.id}`} className="text-base font-medium hover:underline">
        {seller.name}
      </Link>
      {/* §10.1: рейтинг только при наличии отзывов. */}
      {seller.reviews_count > 0 && seller.rating !== null ? (
        <Rating value={seller.rating} reviewsCount={seller.reviews_count} />
      ) : null}
    </span>
  )
}
