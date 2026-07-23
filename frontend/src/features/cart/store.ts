import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Offer, ProductListItem } from '@/shared/api/types'

export interface GuestCartItem {
  /** Ключ позиции: товар + конкретное предложение продавца. */
  key: string
  product: ProductListItem
  offer: Offer | null
  quantity: number
}

interface CartState {
  items: GuestCartItem[]
  add: (product: ProductListItem, offer?: Offer | null, quantity?: number) => void
  setQuantity: (key: string, quantity: number) => void
  remove: (key: string) => void
  clear: () => void
}

export function cartKey(productId: number, offerId: number | null): string {
  return offerId === null ? `p${productId}` : `p${productId}:o${offerId}`
}

/** §7: гостевая корзина — zustand+persist, мерж на бэк при логине. */
export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      items: [],

      add: (product, offer = null, quantity = 1) =>
        set((state) => {
          const key = cartKey(product.id, offer?.id ?? null)
          const existing = state.items.find((item) => item.key === key)
          if (existing) {
            return {
              items: state.items.map((item) =>
                item.key === key ? { ...item, quantity: item.quantity + quantity } : item,
              ),
            }
          }
          return { items: [...state.items, { key, product, offer, quantity: Math.max(1, quantity) }] }
        }),

      // §10.2: количество не опускается ниже 1 — удаление это отдельное действие.
      setQuantity: (key, quantity) =>
        set((state) => ({
          items: state.items.map((item) => (item.key === key ? { ...item, quantity: Math.max(1, quantity) } : item)),
        })),

      remove: (key) => set((state) => ({ items: state.items.filter((item) => item.key !== key) })),
      clear: () => set({ items: [] }),
    }),
    { name: 'linkavto:cart', version: 1 },
  ),
)

export function useCartCount(): number {
  return useCartStore((state) => state.items.reduce((sum, item) => sum + item.quantity, 0))
}

export function useCartItem(productId: number, offerId: number | null = null): GuestCartItem | null {
  const key = cartKey(productId, offerId)
  return useCartStore((state) => state.items.find((item) => item.key === key) ?? null)
}
