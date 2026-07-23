import { ProductCard, ProductGrid } from '@/entities/product/ProductCard'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, PageMeta } from '@/shared/ui'
import { useFavoritesStore } from '@/features/favorites/store'

export function Component() {
  const items = useFavoritesStore((state) => state.items)

  return (
    <>
      <PageMeta title="Избранное — LINKAVTO" canonicalPath="/favorites" noIndex />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        <h1 className="text-xl font-semibold lg:text-2xl">{t('favorites.title')}</h1>

        {items.length === 0 ? (
          <EmptyState
            title={t('favorites.emptyTitle')}
            text={t('favorites.emptyText')}
            action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
          />
        ) : (
          <ProductGrid>
            {items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </ProductGrid>
        )}
      </Container>
    </>
  )
}
