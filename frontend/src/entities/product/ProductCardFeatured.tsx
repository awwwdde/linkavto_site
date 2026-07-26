import { Link } from 'react-router'
import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { Img, PricePill } from '@/shared/ui'

/**
 * §6, §3.4 правило неровной сетки: крупная тёмная карточка — доминанта ленты.
 * Тёмная пауза (§3.4): фон --color-ink, цена — светлая аутлайн-пилюля.
 */
export function ProductCardFeatured({
  product,
  className,
}: {
  product: ProductListItem
  className?: string
}) {
  return (
    <article
      className={cn(
        'group flex flex-col gap-3 rounded-card bg-ink p-4 text-white',
        className,
      )}
    >
      <Link to={`/product/${product.slug}`} className="flex flex-col gap-3">
        <Img
          src={product.image?.card}
          alt={product.image?.alt ?? product.name}
          width={400}
          height={400}
          className="w-full rounded-control"
          wrapperClassName="bg-white/5 text-ink-ghost-dark"
          sizes="(min-width: 1024px) 260px, 60vw"
        />
        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs text-ink-ghost-dark">{product.sku}</span>
          <h3 className="line-clamp-2 text-base text-white">{product.name}</h3>
        </div>
      </Link>

      <div className="mt-auto">
        <PricePill value={product.price} oldValue={product.old_price} tone="dark" />
      </div>
    </article>
  )
}
