import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

export interface Product {
  id: number
  name: string
  slug: string
  part_number: string | null
  price: string
  old_price: string | null
  discount: number
  image: string | null
  url: string
  stock: number
  is_active: boolean
  is_original: boolean
  is_new: boolean
  is_featured: boolean
  average_rating: number
  review_count: number
  has_active_sale: boolean
  description?: string
  short_description?: string
}

export interface Category {
  id: number
  name: string
  slug: string
  icon: string | null
  image: string | null
  url: string
  parent: number | null
  order: number
}

export interface CarouselSlide {
  id: number
  title: string
  image: string | null
  url: string
  order: number
}

export interface HomeData {
  carousel_slides: CarouselSlide[]
  new_products: Product[]
  sale_products: Product[]
  popular_products: Product[]
  featured_products: Product[]
  bestsellers: Product[]
}

export interface CartItem {
  product: Product
  quantity: number
  price: number
  total_price: number
}

export interface CartPayload {
  items: CartItem[]
  total_price: number
  total_quantity: number
}

export const getHome = () => api.get<HomeData>('/home/').then((r) => r.data)
export const getCategories = (parent?: string) =>
  api.get<Category[]>('/categories/', { params: parent ? { parent } : {} }).then((r) => r.data)
export const getProducts = (params: Record<string, unknown>) =>
  api.get('/products/', { params }).then((r) => r.data)
export const getProduct = (slug: string) =>
  api.get<Product>(`/products/${slug}/`).then((r) => r.data)

export const fetchCart = () => api.get<CartPayload>('/cart/').then((r) => r.data)
export const addToCart = (productId: number, quantity = 1, update = false) =>
  api.post<CartPayload>(`/cart/add/${productId}/`, { quantity, update }).then((r) => r.data)
export const removeFromCart = (productId: number) =>
  api.post<CartPayload>(`/cart/remove/${productId}/`, {}).then((r) => r.data)
export const clearCart = () => api.post<CartPayload>('/cart/clear/', {}).then((r) => r.data)
