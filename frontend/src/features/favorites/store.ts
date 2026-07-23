import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ProductListItem } from '@/shared/api/types'

interface FavoritesState {
  items: ProductListItem[]
  toggle: (product: ProductListItem) => void
  remove: (id: number) => void
  has: (id: number) => boolean
}

/** Гостевое избранное; при логине синхронизируется с `favorites/`. */
export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      items: [],
      toggle: (product) =>
        set((state) =>
          state.items.some((item) => item.id === product.id)
            ? { items: state.items.filter((item) => item.id !== product.id) }
            : { items: [product, ...state.items] },
        ),
      remove: (id) => set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
      has: (id) => get().items.some((item) => item.id === id),
    }),
    { name: 'linkavto:favorites', version: 1 },
  ),
)

export const useIsFavorite = (id: number) => useFavoritesStore((state) => state.items.some((item) => item.id === id))
