import { useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import {
  fetchProduct,
  fetchProductOffers,
  fetchProductReviews,
  fetchSimilarProducts,
} from '@/entities/product/api'
import { AttributesTable } from '@/entities/product/AttributesTable'
import { OffersTable, OffersTableSkeleton } from '@/entities/product/OffersTable'
import { PartPassport } from '@/entities/product/PartPassport'
import { ProductCard, ProductGrid } from '@/entities/product/ProductCard'
import { ProductGallery } from '@/entities/product/ProductGallery'
import { ReviewList } from '@/entities/review/ReviewList'
import { ReviewForm } from '@/entities/review/ReviewForm'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import {
  Badge,
  Breadcrumbs,
  ButtonLink,
  Container,
  ErrorState,
  PageMeta,
  Price,
  Rating,
  Skeleton,
} from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { AddToCart } from '@/features/cart/AddToCart'
import { FavoriteButton } from '@/features/favorites/FavoriteButton'
import { ShareButtons } from '@/features/share/ShareButtons'
import { useActiveVehicle } from '@/features/garage/store'

function ProductSkeleton() {
  return (
    <Container className="grid gap-8 py-6 lg:grid-cols-2">
      <Skeleton className="aspect-square w-full rounded-card" />
      <div className="flex flex-col gap-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-12 w-full rounded-control" />
        <Skeleton className="h-40 w-full rounded-card" />
      </div>
    </Container>
  )
}

export function Component() {
  const { slug = '' } = useParams()
  const vehicle = useActiveVehicle()

  const product = useQuery({
    queryKey: queryKeys.products.detail(slug),
    queryFn: () => fetchProduct(slug),
  })

  const offers = useQuery({
    queryKey: queryKeys.products.offers(slug),
    queryFn: () => fetchProductOffers(slug),
    enabled: product.isSuccess,
  })

  const reviews = useQuery({
    queryKey: queryKeys.products.reviews(slug),
    queryFn: () => fetchProductReviews(slug),
    enabled: product.isSuccess && (product.data?.reviews_count ?? 0) > 0,
  })

  const similar = useQuery({
    queryKey: queryKeys.products.similar(slug),
    queryFn: () => fetchSimilarProducts(slug),
    enabled: product.isSuccess,
  })

  if (product.isPending) return <ProductSkeleton />
  if (product.isError) {
    return (
      <Container className="py-12">
        <ErrorState onRetry={() => void product.refetch()} />
      </Container>
    )
  }

  const item = product.data

  return (
    <>
      <PageMeta
        title={`${item.name} — купить в LINKAVTO`}
        description={item.description_plain}
        canonicalPath={`/product/${item.slug}`}
        ogImage={item.image?.full ?? null}
        ogType="product"
      />

      <Container className="flex flex-col gap-10 py-4 lg:py-8">
        <Breadcrumbs
          items={[
            { label: t('nav.home'), to: '/' },
            ...item.breadcrumbs.map((crumb) => ({ label: crumb.name, to: `/category/${crumb.path}` })),
            { label: item.name },
          ]}
        />

        <div className="grid gap-8 lg:grid-cols-2">
          {/* §3.4, правило одной оси: доминанта карточки — галерея. */}
          <ProductGallery images={item.images} name={item.name} />

          <div className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <span className="font-mono text-sm text-ink-muted">{item.sku}</span>
              <h1 className="text-xl font-semibold lg:text-2xl">{item.name}</h1>
              <div className="flex flex-wrap items-center gap-3">
                {item.reviews_count > 0 && item.rating !== null ? (
                  <Rating value={item.rating} reviewsCount={item.reviews_count} />
                ) : null}
                {vehicle && item.fits_vehicle ? <Badge tone="ok">{t('garage.fits')}</Badge> : null}
                <Badge tone={item.in_stock ? 'ok' : 'neutral'}>
                  {item.in_stock ? t('product.inStock') : t('product.outOfStock')}
                </Badge>
              </div>
            </div>

            <div className="flex flex-col gap-4 rounded-card bg-surface p-4 shadow-float">
              <Price value={item.price} oldValue={item.old_price} size="lg" />
              <div className="flex items-center gap-2">
                <div className="min-w-0 flex-1">
                  <AddToCart product={item} size="lg" />
                </div>
                <FavoriteButton product={item} />
              </div>
            </div>

            <PartPassport
              sku={item.sku}
              oemNumber={item.oem_number}
              crosses={item.crosses}
              compatibility={item.compatibility}
            />

            <ShareButtons title={item.name} />
          </div>
        </div>

        {offers.isPending ? <OffersTableSkeleton /> : offers.data ? <OffersTable offers={offers.data} product={item} /> : null}

        <AttributesTable attributes={item.attributes} />

        {item.description_html ? (
          <section className="flex flex-col gap-4">
            <SectionHeading lead={t('product.description')} ghost={t('product.descriptionGhost')} />
            <div
              className="flex flex-col gap-3 rounded-card bg-surface p-4 text-base leading-relaxed text-ink-muted shadow-float lg:p-6 [&_li]:ml-4 [&_li]:list-disc [&_p]:mb-2"
              // §10.5: единственное разрешённое место — описание, санитизировано бэком.
              dangerouslySetInnerHTML={{ __html: item.description_html }}
            />
          </section>
        ) : null}

        {reviews.data ? <ReviewList reviews={reviews.data} /> : null}

        <ReviewForm productSlug={item.slug} />

        {similar.data && similar.data.length > 0 ? (
          <section className="flex flex-col gap-4">
            <SectionHeading lead={t('product.similar')} ghost={t('product.similarGhost')} />
            <ProductGrid>
              {similar.data.slice(0, 8).map((similarItem) => (
                <ProductCard key={similarItem.id} product={similarItem} />
              ))}
            </ProductGrid>
          </section>
        ) : null}

        <div className="lg:hidden">
          <ButtonLink to={`/category/${item.category.path}`} block>
            {t('common.toCatalog')}
          </ButtonLink>
        </div>
      </Container>
    </>
  )
}
