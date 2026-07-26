import type { ReactNode } from 'react'
import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { ProductCard } from '@/entities/product/ProductCard'
import { ProductCardFeatured } from '@/entities/product/ProductCardFeatured'

/**
 * §4б зона 4: лента товаров БЕЗ заголовка — навигация лентой задаётся чипами.
 * Mobile — скролл по X; desktop — сетка. Первая карточка может быть
 * доминантой (ProductCardFeatured, §3.4 правило неровной сетки).
 */
export function ProductRow({
  products,
  featured = false,
  chips,
  label,
  columns = 5,
}: {
  products: ProductListItem[]
  featured?: boolean
  chips?: ReactNode
  label?: ReactNode
  columns?: 4 | 5
}) {
  if (products.length === 0) return null

  const [first, ...rest] = products
  const featuredFirst = featured && first
  const gridCols = columns === 5 ? 'lg:grid-cols-5' : 'lg:grid-cols-4'

  return (
    <div className="flex flex-col gap-3">
      {label ? <div className="text-sm text-ink-muted">{label}</div> : null}
      {chips ? (
        <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:mx-0 lg:px-0">{chips}</div>
      ) : null}

      <div
        className={cn(
          'no-scrollbar -mx-4 flex gap-4 overflow-x-auto px-4',
          'lg:mx-0 lg:grid lg:gap-4 lg:overflow-visible lg:px-0',
          gridCols,
        )}
      >
        {featuredFirst ? (
          <ProductCardFeatured product={first} className="w-52 shrink-0 lg:w-auto" />
        ) : null}
        {(featuredFirst ? rest : products).map((product) => (
          <ProductCard key={product.id} product={product} className="w-40 shrink-0 lg:w-auto" />
        ))}
      </div>
    </div>
  )
}
