import { useState } from 'react'
import { useParams } from 'react-router'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchProducts } from '@/entities/product/api'
import { ProductCard, ProductCardSkeleton, ProductGrid } from '@/entities/product/ProductCard'
import { fetchSeller } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { PAGE_SIZE } from '@/shared/config'
import { t } from '@/shared/i18n'
import { formatPlural } from '@/shared/lib/format'
import {
  Avatar,
  BottomSheet,
  Button,
  ButtonLink,
  Container,
  EmptyState,
  ErrorState,
  PageMeta,
  Pagination,
  Rating,
  Select,
  Skeleton,
} from '@/shared/ui'
import { IconFilter } from '@/shared/ui/Icon'
import { CatalogFilters } from '@/features/catalog-filters/CatalogFilters'
import { SelectedFilters } from '@/features/catalog-filters/SelectedFilters'
import { SORT_OPTIONS, useCatalogParams } from '@/features/catalog-filters/useCatalogParams'

export function Component() {
  const { id = '' } = useParams()
  const { params: filters, setParam, setPage, activeCount, queryParams } = useCatalogParams()
  const [filtersOpen, setFiltersOpen] = useState(false)

  const seller = useQuery({ queryKey: queryKeys.seller(id), queryFn: () => fetchSeller(id) })

  // Товары и фасеты — только этого продавца: мок считает facets из выборки seller.
  const listParams = { seller: Number(id), ...queryParams }
  const products = useQuery({
    queryKey: queryKeys.products.list(listParams),
    queryFn: () => fetchProducts(listParams),
    placeholderData: keepPreviousData,
  })

  if (seller.isError) {
    return (
      <Container className="py-12">
        <ErrorState onRetry={() => void seller.refetch()} />
      </Container>
    )
  }

  const info = seller.data?.seller
  const pageCount = products.data ? Math.ceil(products.data.count / PAGE_SIZE) : 0

  return (
    <>
      <PageMeta
        title={info ? `${info.name} — продавец на LINKAVTO` : t('seller.title')}
        description={info?.description ?? `Товары продавца на маркетплейсе LINKAVTO.`}
        canonicalPath={`/seller/${id}`}
      />

      <Container className="flex flex-col gap-8 py-4 lg:py-8">
        {/* Шапка витрины: баннер + логотип + инфо магазина. */}
        {info ? (
          <header className="overflow-hidden rounded-card bg-surface shadow-float">
            {/* Баннер — фон-подложка; логотип и имя лежат поверх снизу (белым). */}
            <div className="relative h-40 w-full overflow-hidden bg-ink sm:h-48 lg:h-56">
              {info.banner_url ? (
                <>
                  <img src={info.banner_url} alt="" className="absolute inset-0 h-full w-full object-cover" />
                  {/* Затемнение снизу — чтобы белые логотип и имя читались поверх фото. */}
                  <span className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-ink/80 to-transparent" />
                </>
              ) : null}

              <div className="absolute inset-x-0 bottom-0 flex items-end gap-4 p-4 lg:p-6">
                <span className="shrink-0 rounded-card bg-surface p-1 shadow-float">
                  <Avatar src={info.avatar_url} name={info.name} size={80} shape="rounded" />
                </span>
                <div className="flex min-w-0 flex-1 flex-col gap-0.5 pb-1">
                  <h1 className="truncate text-xl font-semibold text-white lg:text-2xl">{info.name}</h1>
                  {info.company_name ? (
                    <span className="truncate text-sm text-white/70">{info.company_name}</span>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-4 p-4 lg:p-6">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-muted">
                {info.reviews_count > 0 && info.rating !== null ? (
                  <Rating value={info.rating} reviewsCount={info.reviews_count} />
                ) : null}
                {info.city ? <span>{info.city}</span> : null}
                {info.since ? (
                  <span>
                    {t('seller.since')} {info.since}
                  </span>
                ) : null}
              </div>

              {info.description ? (
                <p className="max-w-[75ch] text-base text-ink-muted">{info.description}</p>
              ) : null}
            </div>
          </header>
        ) : (
          <Skeleton className="h-64 rounded-card" />
        )}

        {/* Товары магазина + умные фильтры (только по товарам продавца). */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-md font-semibold">
              {t('seller.inStore')}
              {products.data ? (
                <span className="ml-2 text-sm font-normal text-ink-muted">
                  {formatPlural(products.data.count, { one: 'товар', few: 'товара', many: 'товаров' })}
                </span>
              ) : null}
            </h2>

            <div className="flex items-center gap-3">
              <Button className="lg:hidden" onClick={() => setFiltersOpen(true)}>
                <IconFilter width={18} height={18} />
                {t('catalog.filters')}
                {activeCount > 0 ? <span className="tabular-nums">· {activeCount}</span> : null}
              </Button>
              <Select
                aria-label={t('catalog.sort')}
                value={filters.sort}
                onChange={(event) => setParam('sort', event.target.value)}
                wrapperClassName="w-52"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {t(option.labelKey)}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <SelectedFilters className="-mx-4 px-4 lg:mx-0 lg:px-0" />

          <div className="flex gap-8">
            <aside className="hidden w-72 shrink-0 lg:block">
              <div className="sticky top-24 max-h-[calc(100dvh-7rem)] overflow-y-auto rounded-card bg-surface p-4 shadow-float">
                <CatalogFilters data={products.data} />
              </div>
            </aside>

            <div className="min-w-0 flex-1">
              {products.isError ? (
                <ErrorState onRetry={() => void products.refetch()} />
              ) : products.isPending ? (
                <ProductGrid>
                  {Array.from({ length: 6 }, (_, index) => (
                    <ProductCardSkeleton key={index} />
                  ))}
                </ProductGrid>
              ) : products.data.results.length === 0 ? (
                <EmptyState
                  title={t('seller.emptyTitle')}
                  text={t('seller.emptyText')}
                  action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
                />
              ) : (
                <div className="flex flex-col gap-8">
                  <ProductGrid className={products.isFetching ? 'opacity-70 transition-opacity' : undefined}>
                    {products.data.results.map((product) => (
                      <ProductCard key={product.id} product={product} />
                    ))}
                  </ProductGrid>
                  <Pagination page={filters.page} pageCount={pageCount} onChange={setPage} />
                </div>
              )}
            </div>
          </div>
        </section>
      </Container>

      <BottomSheet open={filtersOpen} onClose={() => setFiltersOpen(false)} title={t('catalog.filters')}>
        <CatalogFilters data={products.data} />
        <Button variant="primary" size="lg" block className="mt-6" onClick={() => setFiltersOpen(false)}>
          {t('catalog.filtersApply')}
        </Button>
      </BottomSheet>
    </>
  )
}
