import { useMemo } from 'react'
import { Link } from 'react-router'
import type { SellerBrief } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { formatPlural } from '@/shared/lib/format'
import { ButtonLink, Container, EmptyState, Img, PageMeta, Price, Stepper } from '@/shared/ui'
import { useCartStore, type GuestCartItem } from '@/features/cart/store'

const DEFAULT_SELLER: SellerBrief = {
  id: 0,
  name: 'LINKAVTO',
  slug: 'linkavto',
  rating: null,
  reviews_count: 0,
}

/** Доставка считается по-продавцово (§7). */
const DELIVERY_PER_SELLER = 39000

interface Group {
  seller: SellerBrief
  items: GuestCartItem[]
  subtotal: number
}

export function Component() {
  const items = useCartStore((state) => state.items)
  const setQuantity = useCartStore((state) => state.setQuantity)
  const remove = useCartStore((state) => state.remove)

  const groups = useMemo<Group[]>(() => {
    const map = new Map<number, Group>()
    for (const item of items) {
      const seller = item.offer?.seller ?? DEFAULT_SELLER
      const group = map.get(seller.id) ?? { seller, items: [], subtotal: 0 }
      group.items.push(item)
      group.subtotal += (item.offer?.price ?? item.product.price) * item.quantity
      map.set(seller.id, group)
    }
    return [...map.values()]
  }, [items])

  const subtotal = groups.reduce((sum, group) => sum + group.subtotal, 0)
  const delivery = groups.length * DELIVERY_PER_SELLER
  const count = items.reduce((sum, item) => sum + item.quantity, 0)

  return (
    <>
      <PageMeta title="Корзина — LINKAVTO" canonicalPath="/cart" noIndex />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        <h1 className="text-xl font-semibold lg:text-2xl">{t('cart.title')}</h1>

        {items.length === 0 ? (
          <EmptyState
            title={t('cart.emptyTitle')}
            text={t('cart.emptyText')}
            action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
          />
        ) : (
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
            <div className="flex min-w-0 flex-1 flex-col gap-4">
              {groups.map((group) => (
                <section key={group.seller.id} className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float">
                  <div className="flex items-baseline justify-between gap-3">
                    <h2 className="text-md font-semibold">
                      {group.seller.id === 0 ? (
                        group.seller.name
                      ) : (
                        <Link to={`/seller/${group.seller.id}`} className="hover:underline">
                          {group.seller.name}
                        </Link>
                      )}
                    </h2>
                    <span className="text-sm text-ink-muted">
                      {t('cart.sellerDelivery')} <Price value={DELIVERY_PER_SELLER} size="sm" />
                    </span>
                  </div>

                  <ul className="flex flex-col gap-4">
                    {group.items.map((item) => (
                      <li key={item.key} className="flex gap-3">
                        <Link to={`/product/${item.product.slug}`} className="shrink-0">
                          <Img
                            src={item.product.image?.thumb}
                            alt={item.product.image?.alt ?? item.product.name}
                            width={88}
                            height={88}
                            className="h-22 w-22 rounded-control"
                          />
                        </Link>

                        <div className="flex min-w-0 flex-1 flex-col gap-2">
                          <Link to={`/product/${item.product.slug}`} className="line-clamp-2 text-base">
                            {item.product.name}
                          </Link>
                          <span className="font-mono text-xs text-ink-muted">{item.product.sku}</span>

                          <div className="mt-auto flex flex-wrap items-center justify-between gap-3">
                            <Stepper
                              value={item.quantity}
                              onChange={(next) => setQuantity(item.key, next)}
                              onRemove={() => remove(item.key)}
                            />
                            <Price value={(item.offer?.price ?? item.product.price) * item.quantity} />
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>

            <aside className="w-full shrink-0 lg:sticky lg:top-28 lg:w-80">
              <div className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float">
                <h2 className="text-md font-semibold">{t('cart.total')}</h2>

                <div className="flex justify-between text-base">
                  <span className="text-ink-muted">
                    {t('cart.subtotal')}, {formatPlural(count, { one: 'штука', few: 'штуки', many: 'штук' })}
                  </span>
                  <Price value={subtotal} size="sm" />
                </div>

                <div className="flex justify-between text-base">
                  <span className="text-ink-muted">{t('cart.delivery')}</span>
                  <Price value={delivery} size="sm" />
                </div>

                <div className="flex items-baseline justify-between border-t border-line pt-3">
                  <span className="text-md font-semibold">{t('cart.total')}</span>
                  <Price value={subtotal + delivery} size="lg" />
                </div>

                <ButtonLink to="/checkout" variant="primary" size="lg" block>
                  {t('cart.checkout')}
                </ButtonLink>
              </div>
            </aside>
          </div>
        )}
      </Container>
    </>
  )
}
