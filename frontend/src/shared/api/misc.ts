import { get } from '@/shared/api/client'
import type { Banner, HomeSection, ProductListItem, SellerBrief, StaticPage } from '@/shared/api/types'

export const fetchBanners = () => get<Banner[]>('banners/')

export const fetchHomeSections = () => get<HomeSection[]>('home/sections/')

export const fetchStaticPage = (slug: string) => get<StaticPage>(`pages/${slug}/`)

/**
 * Публичная витрина продавца. Данные магазина в проде приходят из CRM
 * (см. FRONTEND_API.md: store_name/company_name/avatar_url). Баннер и описание
 * витрины CRM пока не отдаёт — TODO(api), временно из мока.
 */
export interface SellerStore {
  description: string | null
  city: string | null
  since: string | null
  company_name: string | null
  /** Логотип магазина (CRM banner.avatar_url). */
  avatar_url: string | null
  /** Обложка витрины. TODO(api). */
  banner_url: string | null
}

export interface SellerPage {
  seller: SellerBrief & SellerStore
  products: ProductListItem[]
}

export const fetchSeller = (id: string) => get<SellerPage>(`sellers/${id}/`)
