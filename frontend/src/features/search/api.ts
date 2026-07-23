import { get } from '@/shared/api/client'
import type { SearchMode, SearchResponse, SearchSuggestion } from '@/shared/api/types'

export const fetchSuggestions = (q: string) => get<SearchSuggestion[]>('search/suggest/', { q })

export interface SearchParams {
  q: string
  type?: SearchMode
  page?: number
  garage_vehicle_id?: number
}

export function fetchSearch({ q, type = 'auto', page = 1, garage_vehicle_id }: SearchParams) {
  const params: Record<string, string | number> = { q, type, page }
  if (garage_vehicle_id) params['garage_vehicle_id'] = garage_vehicle_id
  return get<SearchResponse>('search/', params)
}
