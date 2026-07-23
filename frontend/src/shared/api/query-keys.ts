/** Единый реестр ключей TanStack Query. */
export const queryKeys = {
  categories: {
    tree: () => ['categories', 'tree'] as const,
    detail: (slug: string) => ['categories', 'detail', slug] as const,
  },
  products: {
    list: (params: Record<string, unknown>) => ['products', 'list', params] as const,
    detail: (slug: string) => ['products', 'detail', slug] as const,
    offers: (slug: string) => ['products', 'offers', slug] as const,
    similar: (slug: string) => ['products', 'similar', slug] as const,
    reviews: (slug: string) => ['products', 'reviews', slug] as const,
  },
  search: {
    suggest: (q: string) => ['search', 'suggest', q] as const,
    results: (params: Record<string, unknown>) => ['search', 'results', params] as const,
  },
  garage: {
    vehicles: () => ['garage', 'vehicles'] as const,
    makes: (type: string) => ['garage', 'makes', type] as const,
    models: (makeId: number | null) => ['garage', 'models', makeId] as const,
    modifications: (modelId: number | null) => ['garage', 'modifications', modelId] as const,
  },
  cart: () => ['cart'] as const,
  favorites: () => ['favorites'] as const,
  orders: {
    list: () => ['orders', 'list'] as const,
    detail: (id: string) => ['orders', 'detail', id] as const,
  },
  seller: (id: string) => ['seller', id] as const,
  home: {
    banners: () => ['home', 'banners'] as const,
    sections: () => ['home', 'sections'] as const,
  },
  page: (slug: string) => ['page', slug] as const,
  me: () => ['me'] as const,
} as const
