import type { ProductListItem } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconHeart } from '@/shared/ui/Icon'
import { useFavoritesStore, useIsFavorite } from './store'

export function FavoriteButton({ product, className }: { product: ProductListItem; className?: string }) {
  const isFavorite = useIsFavorite(product.id)
  const toggle = useFavoritesStore((state) => state.toggle)

  return (
    <button
      type="button"
      onClick={() => toggle(product)}
      aria-pressed={isFavorite}
      aria-label={isFavorite ? t('product.fromFavorites') : t('product.toFavorites')}
      className={cn(
        'flex h-10 w-10 items-center justify-center rounded-control transition-colors duration-[--duration-fast]',
        isFavorite ? 'text-danger' : 'text-ink-muted hover:text-ink',
        className,
      )}
    >
      <IconHeart className={isFavorite ? 'fill-current' : undefined} />
    </button>
  )
}
