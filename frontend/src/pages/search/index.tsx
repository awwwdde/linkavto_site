import { Link, useSearchParams } from 'react-router'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ProductCard, ProductCardSkeleton, ProductGrid } from '@/entities/product/ProductCard'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { formatPlural } from '@/shared/lib/format'
import { Badge, ButtonLink, ChipLink, Container, EmptyState, ErrorState, PageMeta, Pagination } from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { fetchSearch } from '@/features/search/api'
import { detectSearchMode } from '@/features/search/detect'
import { GarageContextBar } from '@/features/garage/GarageContextBar'
import { PAGE_SIZE } from '@/shared/config'

const MODE_LABEL = {
  vin: t('search.modeVin'),
  sku: t('search.modeSku'),
  text: t('search.modeText'),
} as const

export function Component() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q') ?? ''
  const page = Math.max(1, Number(searchParams.get('page') ?? 1))
  // Как и в каталоге: подбор под авто управляется URL-параметром (тумблером
  // в GarageContextBar), а не жёстко активным авто из гаража.
  const garageVehicleId = searchParams.get('garage_vehicle_id')
  const mode = detectSearchMode(query)

  const params = {
    q: query,
    type: 'auto' as const,
    page,
    ...(garageVehicleId ? { garage_vehicle_id: Number(garageVehicleId) } : {}),
  }

  const results = useQuery({
    queryKey: queryKeys.search.results(params),
    queryFn: () => fetchSearch(params),
    enabled: query.trim().length >= 2,
    placeholderData: keepPreviousData,
  })

  const setPage = (next: number) => {
    const updated = new URLSearchParams(searchParams)
    if (next > 1) updated.set('page', String(next))
    else updated.delete('page')
    setSearchParams(updated, { preventScrollReset: true })
  }

  const pageCount = results.data ? Math.ceil(results.data.count / PAGE_SIZE) : 0

  return (
    <>
      <PageMeta
        title={`${query} — поиск запчастей в LINKAVTO`}
        description={`Результаты поиска «${query}» в каталоге автозапчастей LINKAVTO.`}
        canonicalPath={`/search?q=${encodeURIComponent(query)}`}
        noIndex
      />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        {/* §3.2 двухтоновый заголовок: запрос + счётчик результатов вторым тоном. */}
        <div className="flex flex-wrap items-center gap-3">
          <SectionHeading
            as="h1"
            size="xl"
            lead={`«${query}».`}
            ghost={
              results.data
                ? formatPlural(results.data.count, { one: 'товар', few: 'товара', many: 'товаров' })
                : undefined
            }
          />
          <Badge>{MODE_LABEL[mode]}</Badge>
        </div>

        {/* Гараж-контекст: тот же тумблер «только подходящие», что и в каталоге. */}
        <GarageContextBar className="sticky top-14 z-20 lg:top-20" />

        {results.data && results.data.vehicle ? (
          <p className="rounded-card bg-surface p-4 text-base shadow-float">
            По VIN определён автомобиль:{' '}
            <Link to="/garage" className="font-medium underline">
              {results.data.vehicle.title}
            </Link>
          </p>
        ) : null}

        {results.data && results.data.categories.length > 0 ? (
          <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:mx-0 lg:px-0">
            {results.data.categories.map((category) => (
              <ChipLink key={category.id} to={`/category/${category.path}`}>
                {category.name}
              </ChipLink>
            ))}
          </div>
        ) : null}

        {query.trim().length < 2 ? (
          <EmptyState
            title={t('search.emptyTitle')}
            text={t('search.emptyText')}
            action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
          />
        ) : results.isError ? (
          <ErrorState onRetry={() => void results.refetch()} />
        ) : results.isPending ? (
          <ProductGrid>
            {Array.from({ length: 8 }, (_, index) => (
              <ProductCardSkeleton key={index} />
            ))}
          </ProductGrid>
        ) : results.data.results.length === 0 ? (
          <EmptyState
            title={t('search.emptyTitle')}
            text={t('search.emptyText')}
            action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
          />
        ) : (
          <div className="flex flex-col gap-8">
            <ProductGrid className={results.isFetching ? 'opacity-70 transition-opacity' : undefined}>
              {results.data.results.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </ProductGrid>
            <Pagination page={page} pageCount={pageCount} onChange={setPage} />
          </div>
        )}
      </Container>
    </>
  )
}
