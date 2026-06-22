import { create } from 'zustand'
import {
  fetchCart,
  addToCart as apiAdd,
  removeFromCart as apiRemove,
  clearCart as apiClear,
  type CartPayload,
} from '../api'

interface CartState {
  items: CartPayload['items']
  totalPrice: number
  totalQuantity: number
  loading: boolean
  load: () => Promise<void>
  add: (productId: number, quantity?: number) => Promise<void>
  remove: (productId: number) => Promise<void>
  clear: () => Promise<void>
  isInCart: (productId: number) => boolean
}

function apply(set: (p: Partial<CartState>) => void, data: CartPayload) {
  set({
    items: data.items,
    totalPrice: data.total_price,
    totalQuantity: data.total_quantity,
  })
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  totalPrice: 0,
  totalQuantity: 0,
  loading: false,
  load: async () => {
    set({ loading: true })
    try {
      apply(set, await fetchCart())
    } finally {
      set({ loading: false })
    }
  },
  add: async (productId, quantity = 1) => {
    apply(set, await apiAdd(productId, quantity))
  },
  remove: async (productId) => {
    apply(set, await apiRemove(productId))
  },
  clear: async () => {
    apply(set, await apiClear())
  },
  isInCart: (productId) => get().items.some((i) => i.product.id === productId),
}))
