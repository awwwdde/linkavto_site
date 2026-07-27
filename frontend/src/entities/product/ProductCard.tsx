import { Link } from 'react-router'
import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { Badge, Img, Price, Rating, Skeleton } from '@/shared/ui'
import { AddToCart } from '@/features/cart/AddToCart'

/**
 * §3.4: минималистичная карточка — вертикальный прямоугольник (высота > ширины).
 * Фото флешит к верху и краям карточки, ниже — название, строка «цена + оценка»
 * и кнопка в корзину. Единственный бейдж — «подходит авто» (§3.4); скидка —
 * зачёркнутой ценой, не бейджем (§3.1).
 */
export function ProductCard({ product, className }: { product: ProductListItem; className?: string }) {
  const fits = product.fits_vehicle === true
  const badge = fits ? <Badge tone="ok">{t('garage.fits')}</Badge> : null
  const showRating = product.reviews_count > 0 && product.rating !== null

  return (
    <article
      className={cn(
        'group flex flex-col overflow-hidden rounded-card border bg-surface',
        // Подходит выбранному авто → спокойная ok-обводка (§ гараж-контекст).
        fits ? 'border-ok/30' : 'border-line',
        'transition-shadow duration-[--duration-base] hover:shadow-float',
        className,
      )}
    >
      <Link to={`/product/${product.slug}`} className="flex flex-col">
        {/* Фото во всю ширину, доходит до верха и краёв карточки. */}
        <div className="relative overflow-hidden bg-paper">
          <Img
            src={product.image?.card}
            alt={product.image?.alt ?? product.name}
            width={400}
            height={500}
            cover
            className="aspect-[4/5] w-full transition-transform duration-500 group-hover:scale-[1.03]"
            sizes="(min-width: 1024px) 260px, 45vw"
          />
          {badge ? <span className="absolute top-2 left-2">{badge}</span> : null}
        </div>

        <div className="flex flex-col gap-2 p-3">
          <h3 className="line-clamp-2 min-h-[2.75em] text-sm text-ink lg:text-base">{product.name}</h3>
          <div className="flex items-center justify-between gap-2">
            <Price value={product.price} oldValue={product.old_price} size="md" />
            {showRating ? (
              <Rating value={product.rating!} reviewsCount={product.reviews_count} showCount={false} />
            ) : null}
          </div>
        </div>
      </Link>

      <div className="mt-auto p-3 pt-0">
        <AddToCart product={product} />
      </div>
    </article>
  )
}

export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-card border border-line bg-surface">
      <Skeleton className="aspect-[4/5] w-full rounded-none" />
      <div className="flex flex-col gap-2 p-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <div className="flex items-center justify-between pt-1">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-4 w-10" />
        </div>
        <Skeleton className="mt-1 h-10 w-full rounded-control" />
      </div>
    </div>
  )
}

export function ProductGrid({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4', className)}>{children}</div>
  )
}
