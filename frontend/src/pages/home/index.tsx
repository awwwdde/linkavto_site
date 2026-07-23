import { Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { fetchCategoryTree } from '@/entities/category/api'
import { CategoryTile } from '@/entities/category/CategoryTile'
import { ProductCard, ProductCardSkeleton, ProductGrid } from '@/entities/product/ProductCard'
import { fetchHomeSections } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { vehicleMeta } from '@/shared/lib/vehicle-types'
import { Container, ErrorState, PageMeta, Section, Skeleton } from '@/shared/ui'
import { IconArrowRight } from '@/shared/ui/Icon'
import { SmartSearch } from '@/features/search/SmartSearch'
import { GarageChip } from '@/features/garage/GarageChip'

/** §3.4, правило одной оси: доминанта главной — поиск. */
function Hero() {
  return (
    <section className="flex flex-col items-center gap-6 py-10 text-center lg:py-16">
      <h1 className="max-w-[18ch] font-display text-xl leading-tight lg:text-2xl">{t('home.heroTitle')}</h1>
      <p className="max-w-[46ch] text-md text-ink-muted">{t('home.heroSubtitle')}</p>
      <div className="w-full max-w-[720px]">
        <SmartSearch showGarageChip={false} />
      </div>
      <GarageChip />
    </section>
  )
}

function VehicleTypes() {
  const tree = useQuery({ queryKey: queryKeys.categories.tree(), queryFn: fetchCategoryTree })

  if (tree.isPending) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }, (_, index) => (
          <Skeleton key={index} className="h-36 rounded-card" />
        ))}
      </div>
    )
  }

  if (tree.isError) return <ErrorState onRetry={() => void tree.refetch()} />

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      {tree.data.map((node) => (
        <CategoryTile
          key={node.id}
          to={`/category/${node.path}`}
          name={node.name}
          productsCount={node.products_count}
          meta={vehicleMeta(node.vehicle_type)}
        />
      ))}
    </div>
  )
}

function HomeSections() {
  const sections = useQuery({ queryKey: queryKeys.home.sections(), queryFn: fetchHomeSections })

  if (sections.isPending) {
    return (
      <div className="flex flex-col gap-10">
        {Array.from({ length: 2 }, (_, index) => (
          <div key={index} className="flex flex-col gap-4">
            <Skeleton className="h-6 w-48" />
            <ProductGrid>
              {Array.from({ length: 4 }, (_, cardIndex) => (
                <ProductCardSkeleton key={cardIndex} />
              ))}
            </ProductGrid>
          </div>
        ))}
      </div>
    )
  }

  if (sections.isError) return <ErrorState onRetry={() => void sections.refetch()} />

  return (
    <div className="flex flex-col gap-10">
      {sections.data
        .filter((section) => section.products.length > 0)
        .map((section) => (
          <Section
            key={section.id}
            title={section.title}
            action={
              section.url ? (
                <Link
                  to={section.url}
                  className="flex min-h-10 items-center gap-1 text-base text-ink-muted hover:text-ink"
                >
                  {t('home.showAll')}
                  <IconArrowRight width={16} height={16} />
                </Link>
              ) : null
            }
          >
            <ProductGrid>
              {section.products.slice(0, 8).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </ProductGrid>
          </Section>
        ))}
    </div>
  )
}

export function Component() {
  return (
    <>
      <PageMeta
        title="LINKAVTO — маркетплейс автозапчастей"
        description="Подбор автозапчастей по VIN, артикулу и гаражу. Легковые, грузовые, мото и спецтехника от проверенных продавцов."
        canonicalPath="/"
      />
      <Container className="flex flex-col gap-12 pb-12">
        <Hero />
        <Section title={t('home.vehicleTypes')}>
          <VehicleTypes />
        </Section>
        <HomeSections />
      </Container>
    </>
  )
}
