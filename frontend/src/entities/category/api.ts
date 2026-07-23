import { get } from '@/shared/api/client'
import type { CategoryDetail, CategoryNode } from '@/shared/api/types'

export const fetchCategoryTree = () => get<CategoryNode[]>('categories/tree/')

export const fetchCategory = (slug: string) => get<CategoryDetail>(`categories/${slug}/`)
