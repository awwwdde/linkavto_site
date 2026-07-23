import { get } from '@/shared/api/client'
import type { Offer, ProductDetail, ProductListItem, ProductListResponse, Review } from '@/shared/api/types'

export interface ProductListParams {
  category?: string
  page?: number
  page_size?: number
  ordering?: string
  price_min?: number
  price_max?: number
  manufacturer?: string
  in_stock?: boolean
  garage_vehicle_id?: number
  seller?: number
}

export function fetchProducts(params: ProductListParams) {
  const search: Record<string, string | number | boolean> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search[key] = value
  }
  return get<ProductListResponse>('products/', search)
}

export const fetchProduct = (slug: string) => get<ProductDetail>(`products/${slug}/`)

export const fetchProductOffers = (slug: string) => get<Offer[]>(`products/${slug}/offers/`)

export const fetchSimilarProducts = (slug: string) => get<ProductListItem[]>(`products/${slug}/similar/`)

export const fetchProductReviews = (slug: string) => get<Review[]>(`products/${slug}/reviews/`)
