import { useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { ProductCard, ProductCardSkeleton, ProductGrid } from '@/entities/product/ProductCard'
import { fetchSeller } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, ErrorState, PageMeta, Rating, Section, Skeleton } from '@/shared/ui'

export function Component() {
  const { id = '' } = useParams()
  const seller = useQuery({ queryKey: queryKeys.seller(id), queryFn: () => fetchSeller(id) })

  if (seller.isPending) {
    return (
      <Container className="flex flex-col gap-6 py-6">
        <Skeleton className="h-24 rounded-card" />
        <ProductGrid>
          {Array.from({ length: 8 }, (_, index) => (
            <ProductCardSkeleton key={index} />
          ))}
        </ProductGrid>
      </Container>
    )
  }

  if (seller.isError) {
    return (
      <Container className="py-12">
        <ErrorState onRetry={() => void seller.refetch()} />
      </Container>
    )
  }

  const { seller: info, products } = seller.data

  return (
    <>
      <PageMeta
        title={`${info.name} — продавец на LINKAVTO`}
        description={info.description ?? `Товары продавца ${info.name} на маркетплейсе LINKAVTO.`}
        canonicalPath={`/seller/${id}`}
      />

      <Container className="flex flex-col gap-8 py-4 lg:py-8">
        <header className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float lg:p-6">
          <h1 className="text-xl font-semibold lg:text-2xl">{info.name}</h1>
          {info.reviews_count > 0 && info.rating !== null ? (
            <Rating value={info.rating} reviewsCount={info.reviews_count} />
          ) : null}
          {info.description ? <p className="max-w-[70ch] text-base text-ink-muted">{info.description}</p> : null}
          {info.city ? <p className="text-sm text-ink-muted">{info.city}</p> : null}
        </header>

        <Section title={t('seller.products')}>
          {products.length === 0 ? (
            <EmptyState
              title={t('seller.emptyTitle')}
              text={t('seller.emptyText')}
              action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
            />
          ) : (
            <ProductGrid>
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </ProductGrid>
          )}
        </Section>
      </Container>
    </>
  )
}
