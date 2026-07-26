import type { Offer, ProductListItem } from '@/shared/api/types'
import { formatDeliveryDays } from '@/shared/lib/format'
import { t } from '@/shared/i18n'
import { Badge, Price, Skeleton } from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { SellerBadge } from '@/entities/seller/SellerBadge'
import { AddToCart } from '@/features/cart/AddToCart'

/** §1: карточка = сравнение предложений. Mobile — карточками, desktop — таблицей. */
export function OffersTable({ offers, product }: { offers: Offer[]; product: ProductListItem }) {
  if (offers.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <SectionHeading lead={t('product.offers')} ghost={t('product.offersGhost')} />

      {/* Mobile */}
      <ul className="flex flex-col gap-3 lg:hidden">
        {offers.map((offer) => (
          <li key={offer.id} className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float">
            <div className="flex items-start justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-base font-medium">{offer.manufacturer}</span>
                {offer.is_original ? <Badge tone="ok">{t('product.original')}</Badge> : null}
              </div>
              <Price value={offer.price} size="md" />
            </div>
            <div className="flex items-end justify-between gap-3">
              <div className="flex flex-col gap-1 text-sm text-ink-muted">
                <SellerBadge seller={offer.seller} />
                <span>{formatDeliveryDays(offer.delivery_days)}</span>
              </div>
              <AddToCart product={product} offer={offer} block={false} />
            </div>
          </li>
        ))}
      </ul>

      {/* Desktop */}
      <div className="hidden overflow-hidden rounded-card bg-surface shadow-float lg:block">
        <table className="w-full border-collapse text-base">
          <thead>
            <tr className="border-b border-line text-left text-sm text-ink-muted">
              <th scope="col" className="px-4 py-3 font-medium">
                {t('product.offersManufacturer')}
              </th>
              <th scope="col" className="px-4 py-3 font-medium">
                {t('product.offersSeller')}
              </th>
              <th scope="col" className="px-4 py-3 font-medium">
                {t('product.offersDelivery')}
              </th>
              <th scope="col" className="px-4 py-3 text-right font-medium">
                {t('product.offersPrice')}
              </th>
              <th scope="col" className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3">
                  <span className="flex items-center gap-2">
                    {offer.manufacturer}
                    {offer.is_original ? <Badge tone="ok">{t('product.original')}</Badge> : null}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <SellerBadge seller={offer.seller} />
                </td>
                <td className="px-4 py-3 text-ink-muted tabular-nums">{formatDeliveryDays(offer.delivery_days)}</td>
                <td className="px-4 py-3 text-right font-mono tabular-nums">
                  <Price value={offer.price} size="md" />
                </td>
                <td className="px-4 py-3 text-right">
                  <AddToCart product={product} offer={offer} block={false} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export function OffersTableSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-6 w-56" />
      {Array.from({ length: 3 }, (_, index) => (
        <Skeleton key={index} className="h-20 rounded-card" />
      ))}
    </div>
  )
}
