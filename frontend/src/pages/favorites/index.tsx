import { ProductCard, ProductGrid } from '@/entities/product/ProductCard'
import { t } from '@/shared/i18n'
import { formatPlural } from '@/shared/lib/format'
import { ButtonLink, Container, EmptyState, PageMeta } from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { useFavoritesStore } from '@/features/favorites/store'

export function Component() {
  const items = useFavoritesStore((state) => state.items)

  return (
    <>
      <PageMeta title="Избранное — LINKAVTO" canonicalPath="/favorites" noIndex />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        {/* §3.2 двухтоновый заголовок: раздел + счётчик вторым тоном. */}
        <SectionHeading
          as="h1"
          size="xl"
          lead={`${t('favorites.title')}.`}
          ghost={
            items.length > 0
              ? formatPlural(items.length, { one: 'товар', few: 'товара', many: 'товаров' })
              : undefined
          }
        />

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
