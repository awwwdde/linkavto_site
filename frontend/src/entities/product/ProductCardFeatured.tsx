import { Link } from 'react-router'
import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { Img, Price } from '@/shared/ui'

/**
 * §6, §3.4 правило неровной сетки: тёмная карточка-доминанта ленты.
 * Тёмная пауза (§3.4): фон --color-ink. Чтобы светлое фото не било стыком по
 * тёмному, оно лежит в аккуратной «рамке» — скруглённый колодец bg-white/5 с
 * равными отступами; ниже название и цена светлым.
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
        'group flex flex-col rounded-card bg-ink p-3 text-white',
        'transition-shadow duration-[--duration-base] hover:shadow-lift',
        className,
      )}
    >
      <Link to={`/product/${product.slug}`} className="flex flex-1 flex-col gap-3">
        <div className="overflow-hidden rounded-control bg-white/5">
          <Img
            src={product.image?.card}
            alt={product.image?.alt ?? product.name}
            width={400}
            height={500}
            cover
            className="aspect-[4/5] w-full transition-transform duration-500 group-hover:scale-[1.03]"
            sizes="(min-width: 1024px) 260px, 60vw"
          />
        </div>

        <div className="mt-auto flex flex-col gap-1.5 px-1 pb-1">
          <h3 className="line-clamp-2 min-h-[2.75em] text-base text-white">{product.name}</h3>
          <Price value={product.price} oldValue={product.old_price} size="md" tone="dark" className="text-white" />
        </div>
      </Link>
    </article>
  )
}
