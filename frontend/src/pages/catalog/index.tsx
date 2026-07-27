import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchCategory } from '@/entities/category/api'
import { categoryHref, slugFromPath, vehicleQuery } from '@/entities/category/tree'
import { fetchProducts } from '@/entities/product/api'
import { ProductCard, ProductCardSkeleton, ProductGrid } from '@/entities/product/ProductCard'
import { queryKeys } from '@/shared/api/query-keys'
import { PAGE_SIZE } from '@/shared/config'
import { t } from '@/shared/i18n'
import { formatPlural } from '@/shared/lib/format'
import {
  BottomSheet,
  Breadcrumbs,
  Button,
  ButtonLink,
  ChipLink,
  Container,
  EmptyState,
  ErrorState,
  PageMeta,
  Pagination,
  Select,
  Skeleton,
} from '@/shared/ui'
import { IconFilter } from '@/shared/ui/Icon'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { GarageContextBar } from '@/features/garage/GarageContextBar'
import { CatalogFilters } from '@/features/catalog-filters/CatalogFilters'
import { SelectedFilters } from '@/features/catalog-filters/SelectedFilters'
import { SORT_OPTIONS, useCatalogParams } from '@/features/catalog-filters/useCatalogParams'

export function Component() {
  const routeParams = useParams()
  /** Путь может быть любой глубины: /category/a/b/c/d/e */
  const path = (routeParams['*'] ?? '').replace(/\/+$/, '')
  const slug = slugFromPath(path)
  const parentPath = path.split('/').slice(0, -1).join('/')
  const [searchParams] = useSearchParams()
  // Подбор под авто переносится в соседние категории вместе с пользователем.
  const keepQuery = vehicleQuery(searchParams)

  const { params: filters, setParam, setPage, activeCount, queryParams } = useCatalogParams()
  const [filtersOpen, setFiltersOpen] = useState(false)

  const category = useQuery({
    queryKey: queryKeys.categories.detail(slug),
    queryFn: () => fetchCategory(slug),
    enabled: slug.length > 0,
  })

  const listParams = { category: slug, ...queryParams }

  const products = useQuery({
    queryKey: queryKeys.products.list(listParams),
    queryFn: () => fetchProducts(listParams),
    // §7: при смене фильтра список не мигает.
    placeholderData: keepPreviousData,
    enabled: slug.length > 0,
  })

  const pageCount = products.data ? Math.ceil(products.data.count / PAGE_SIZE) : 0
  const title = category.data?.name ?? t('catalog.title')
  const children = category.data?.children ?? []

  return (
    <>
      <PageMeta
        title={`${title} — каталог LINKAVTO`}
        description={`${title}: подбор запчастей под конкретный автомобиль — по марке, модели, поколению и модификации.`}
        canonicalPath={`/category/${path}`}
      />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        {category.data ? (
          <Breadcrumbs
            items={[
              { label: t('nav.home'), to: '/' },
              ...category.data.breadcrumbs.map((crumb, index, all) => ({
                label: crumb.name,
                to: index === all.length - 1 ? undefined : categoryHref(crumb.path),
              })),
            ]}
          />
        ) : (
          <Skeleton className="h-4 w-64" />
        )}

        {/* §3.2 двухтоновый заголовок: категория + счётчик товаров вторым тоном. */}
        <SectionHeading
          as="h1"
          size="xl"
          lead={`${title}.`}
          ghost={
            products.data
              ? formatPlural(products.data.count, { one: 'товар', few: 'товара', many: 'товаров' })
              : undefined
          }
        />

        {/* Гараж-контекст: сквозная липкая полоса подбора под конкретное авто. */}
        <GarageContextBar className="sticky top-14 z-20 lg:top-20" />

        {/* Подуровни текущей категории — лента чипов, работает на любой глубине.
            Активный чип подсвечен, «Все» возвращает на текущий уровень. */}
        {category.data && (children.length > 0 || category.data.siblings.length > 1) ? (
          <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:mx-0 lg:px-0">
            {children.length > 0 ? (
              <>
                <ChipLink to={categoryHref(category.data.path, keepQuery)} active>
                  {t('common.all')}
                </ChipLink>
                {children.map((child) => (
                  <ChipLink key={child.id} to={categoryHref(child.path, keepQuery)}>
                    {child.name}
                  </ChipLink>
                ))}
              </>
            ) : (
              <>
                {parentPath ? (
                  <ChipLink to={categoryHref(parentPath, keepQuery)}>{t('common.all')}</ChipLink>
                ) : null}
                {category.data.siblings.map((sibling) => (
                  <ChipLink
                    key={sibling.id}
                    to={categoryHref(sibling.path, keepQuery)}
                    active={sibling.slug === slug}
                  >
                    {sibling.name}
                  </ChipLink>
                ))}
              </>
            )}
          </div>
        ) : null}

        {/* Выбранные фильтры — выделенные теги, снимаются одним нажатием */}
        <SelectedFilters className="-mx-4 px-4 lg:mx-0 lg:px-0" />

        <div className="flex items-center justify-between gap-3">
          <Button className="lg:hidden" onClick={() => setFiltersOpen(true)}>
            <IconFilter width={18} height={18} />
            {t('catalog.filters')}
            {activeCount > 0 ? <span className="tabular-nums">· {activeCount}</span> : null}
          </Button>

          <Select
            aria-label={t('catalog.sort')}
            value={filters.sort}
            onChange={(event) => setParam('sort', event.target.value)}
            wrapperClassName="ml-auto w-56"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {t(option.labelKey)}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex gap-8">
          <aside className="hidden w-72 shrink-0 lg:block">
            <div className="sticky top-36 max-h-[calc(100dvh-10rem)] overflow-y-auto rounded-card bg-surface p-4 shadow-float">
              <CatalogFilters data={products.data} category={category.data} />
            </div>
          </aside>

          <div className="min-w-0 flex-1">
            {products.isError ? (
              <ErrorState onRetry={() => void products.refetch()} />
            ) : products.isPending ? (
              <ProductGrid>
                {Array.from({ length: 8 }, (_, index) => (
                  <ProductCardSkeleton key={index} />
                ))}
              </ProductGrid>
            ) : products.data.results.length === 0 ? (
              <EmptyState
                title={t('catalog.emptyTitle')}
                text={t('catalog.emptyText')}
                action={
                  category.data && category.data.breadcrumbs.length > 1 ? (
                    <ButtonLink to={categoryHref(category.data.breadcrumbs[category.data.breadcrumbs.length - 2]!.path)}>
                      {t('catalog.upOneLevel')}
                    </ButtonLink>
                  ) : (
                    <ButtonLink to="/">{t('common.toHome')}</ButtonLink>
                  )
                }
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

            {/* Глубокие ветки: полный список потомков внизу — для SEO и обхода */}
            {children.length > 0 ? (
              <nav aria-label={t('catalog.subcategories')} className="mt-10 flex flex-col gap-2">
                <h2 className="text-md font-semibold">{t('catalog.subcategories')}</h2>
                <ul className="grid gap-x-6 gap-y-1 sm:grid-cols-2 lg:grid-cols-3">
                  {children.map((child) => (
                    <li key={child.id}>
                      <Link
                        to={categoryHref(child.path, keepQuery)}
                        className="flex min-h-10 items-center justify-between gap-3 text-base text-ink-muted hover:text-ink"
                      >
                        <span className="truncate">{child.name}</span>
                        <span className="shrink-0 text-sm tabular-nums">{child.products_count}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            ) : null}
          </div>
        </div>
      </Container>

      <BottomSheet open={filtersOpen} onClose={() => setFiltersOpen(false)} title={t('catalog.filters')}>
        <CatalogFilters data={products.data} category={category.data} />
        <Button variant="primary" size="lg" block className="mt-6" onClick={() => setFiltersOpen(false)}>
          {t('catalog.filtersApply')}
        </Button>
      </BottomSheet>
    </>
  )
}
