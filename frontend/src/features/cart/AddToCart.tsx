import type { Offer, ProductListItem } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { Button, Stepper } from '@/shared/ui'
import { cartKey, useCartItem, useCartStore } from './store'

export interface AddToCartProps {
  product: ProductListItem
  offer?: Offer | null
  size?: 'md' | 'lg'
  block?: boolean
}

/** §7: после «В корзину» кнопка превращается в степпер (паттерн Ozon/WB). */
export function AddToCart({ product, offer = null, size = 'md', block = true }: AddToCartProps) {
  const item = useCartItem(product.id, offer?.id ?? null)
  const add = useCartStore((state) => state.add)
  const setQuantity = useCartStore((state) => state.setQuantity)
  const remove = useCartStore((state) => state.remove)

  if (!product.in_stock) {
    return (
      <Button size={size} block={block} disabled>
        {t('product.outOfStock')}
      </Button>
    )
  }

  if (item) {
    const key = cartKey(product.id, offer?.id ?? null)
    return (
      <Stepper
        value={item.quantity}
        onChange={(next) => setQuantity(key, next)}
        onRemove={() => remove(key)}
        className={block ? 'w-full justify-between' : undefined}
      />
    )
  }

  return (
    <Button variant="primary" size={size} block={block} onClick={() => add(product, offer)}>
      {t('product.addToCart')}
    </Button>
  )
}
