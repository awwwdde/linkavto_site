import { Link } from 'react-router'
import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { Badge, Img, Price, Rating, Skeleton } from '@/shared/ui'
import { AddToCart } from '@/features/cart/AddToCart'

/**
 * §3.4: карточка в списке несёт максимум фото, название, артикул, цену,
 * рейтинг и кнопку. Не более одного бейджа — остальное в detail.
 */
export function ProductCard({ product, className }: { product: ProductListItem; className?: string }) {
  const badge =
    product.fits_vehicle === true ? (
      <Badge tone="ok">{t('garage.fits')}</Badge>
    ) : product.discount_percent ? (
      <Badge tone="discount">−{product.discount_percent}%</Badge>
    ) : null

  return (
    <article
      className={cn(
        'group flex flex-col gap-3 rounded-card border border-line bg-surface p-3 lg:p-4',
        'transition-[border-color,transform] duration-[--duration-base]',
        className,
      )}
    >
      <Link to={`/product/${product.slug}`} className="relative flex flex-col gap-3">
        <div className="relative">
          <Img
            src={product.image?.card}
            alt={product.image?.alt ?? product.name}
            width={400}
            height={400}
            className="w-full rounded-control"
            sizes="(min-width: 1024px) 260px, 45vw"
          />
          {badge ? <span className="absolute top-2 left-2">{badge}</span> : null}
        </div>

        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs text-ink-muted">{product.sku}</span>
          <h3 className="line-clamp-2 text-base text-ink">{product.name}</h3>
        </div>
      </Link>

      {/* §10.1: рейтинг только при наличии отзывов. */}
      {product.reviews_count > 0 && product.rating !== null ? (
        <Rating value={product.rating} reviewsCount={product.reviews_count} showCount={false} />
      ) : null}

      <div className="mt-auto flex flex-col gap-3">
        <Price value={product.price} oldValue={product.old_price} size="md" />
        <AddToCart product={product} />
      </div>
    </article>
  )
}

export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col gap-3 rounded-card border border-line bg-surface p-3 lg:p-4">
      <Skeleton className="aspect-square w-full" />
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-6 w-28" />
      <Skeleton className="h-10 w-full rounded-control" />
    </div>
  )
}

export function ProductGrid({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4', className)}>{children}</div>
  )
}
