import { get } from '@/shared/api/client'
import type { Banner, HomeSection, ProductListItem, SellerBrief, StaticPage } from '@/shared/api/types'

export const fetchBanners = () => get<Banner[]>('banners/')

export const fetchHomeSections = () => get<HomeSection[]>('home/sections/')

export const fetchStaticPage = (slug: string) => get<StaticPage>(`pages/${slug}/`)

export interface SellerPage {
  seller: SellerBrief & { description: string | null; city: string | null; since: string | null }
  products: ProductListItem[]
}

export const fetchSeller = (id: string) => get<SellerPage>(`sellers/${id}/`)
