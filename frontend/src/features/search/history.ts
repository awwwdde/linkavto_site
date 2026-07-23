import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const LIMIT = 8

interface SearchHistoryState {
  items: string[]
  push: (query: string) => void
  clear: () => void
}

/** §6: история поиска — localStorage. */
export const useSearchHistory = create<SearchHistoryState>()(
  persist(
    (set) => ({
      items: [],
      push: (query) =>
        set((state) => {
          const value = query.trim()
          if (value.length < 2) return state
          return { items: [value, ...state.items.filter((item) => item !== value)].slice(0, LIMIT) }
        }),
      clear: () => set({ items: [] }),
    }),
    { name: 'linkavto:search-history', version: 1 },
  ),
)
