import type { CategoryNode } from '@/shared/api/types'

/** Максимальная глубина дерева категорий (§ требование заказчика). */
export const MAX_CATEGORY_DEPTH = 5

/** Плоский список всех узлов дерева. */
export function flattenTree(nodes: CategoryNode[]): CategoryNode[] {
  return nodes.flatMap((node) => [node, ...flattenTree(node.children)])
}

/**
 * Цепочка от корня до узла с указанным слагом.
 * Слаг в Django глобально уникален, поэтому ищем по последнему сегменту пути.
 */
export function findChain(nodes: CategoryNode[], slug: string): CategoryNode[] {
  for (const node of nodes) {
    if (node.slug === slug) return [node]
    const nested = findChain(node.children, slug)
    if (nested.length > 0) return [node, ...nested]
  }
  return []
}

export function findNode(nodes: CategoryNode[], slug: string): CategoryNode | null {
  const chain = findChain(nodes, slug)
  return chain.length > 0 ? (chain[chain.length - 1] ?? null) : null
}

/** Последний сегмент URL — он и есть идентификатор категории. */
export function slugFromPath(path: string): string {
  const segments = path.split('/').filter(Boolean)
  return segments[segments.length - 1] ?? ''
}

/** Ссылка на категорию: полный путь предков для читаемого URL и хлебных крошек. */
export function categoryHref(path: string, keepQuery?: string): string {
  return keepQuery ? `/category/${path}?${keepQuery}` : `/category/${path}`
}

/**
 * Параметры подбора техники переживают переход между категориями:
 * пользователь ищет детали под одну машину, и терять выбор при смене
 * раздела нельзя.
 */
const VEHICLE_QUERY_KEYS = [
  'vehicle_type',
  'car_type',
  'truck_type',
  'moto_type',
  'special_type',
  'brand',
  'model',
  'generation',
  'modification',
  'garage_vehicle_id',
]

export function vehicleQuery(searchParams: URLSearchParams): string {
  const kept = new URLSearchParams()
  for (const key of VEHICLE_QUERY_KEYS) {
    const value = searchParams.get(key)
    if (value) kept.set(key, value)
  }
  return kept.toString()
}
