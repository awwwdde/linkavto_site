import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router'
import type { VehicleKind } from '@/shared/api/types'
import { PAGE_SIZE } from '@/shared/config'

/**
 * Имена GET-параметров один в один повторяют shop/views.py (category_view),
 * чтобы фронт и Django говорили на одном языке и ничего не пришлось
 * переименовывать на стороне бэкенда.
 *
 * Мультизначные параметры бэк принимает и как `?brand=a&brand=b`,
 * и как `?brand=a,b` — используем второй формат, он короче в ссылке.
 */

export const SORT_OPTIONS = [
  { value: 'popular', labelKey: 'catalog.sortPopular' },
  { value: 'price_asc', labelKey: 'catalog.sortCheap' },
  { value: 'price_desc', labelKey: 'catalog.sortExpensive' },
  { value: 'newest', labelKey: 'catalog.sortNew' },
] as const

export const DEFAULT_SORT = 'popular'

/** Ключ параметра класса техники зависит от типа: car_type/truck_type/… */
export const CLASS_PARAM: Record<VehicleKind, string> = {
  car: 'car_type',
  truck: 'truck_type',
  moto: 'moto_type',
  special: 'special_type',
}

export const TIRE_WHEEL_KEYS = [
  'tire_wheel_type',
  'tire_diameter',
  'tire_width',
  'tire_height',
  'tire_seasonality',
  'tire_spikes',
  'wheel_diameter',
  'wheel_width',
  'wheel_pcd',
  'wheel_offset_type',
  'wheel_type',
] as const

export type TireWheelKey = (typeof TIRE_WHEEL_KEYS)[number]

/** Порядок уровней подбора — от общего к частному. */
export const VEHICLE_LEVELS = [
  'vehicleType',
  'vehicleClass',
  'brand',
  'model',
  'generation',
  'modification',
] as const

export type VehicleLevel = (typeof VEHICLE_LEVELS)[number]

export interface VehicleSelection {
  vehicleType: VehicleKind | null
  vehicleClass: string | null
  brand: string | null
  model: string | null
  generation: string | null
  modification: string | null
}

/** Имя GET-параметра для уровня (класс зависит от типа техники, см. CLASS_PARAM). */
const VEHICLE_PARAM: Record<Exclude<VehicleLevel, 'vehicleClass'>, string> = {
  vehicleType: 'vehicle_type',
  brand: 'brand',
  model: 'model',
  generation: 'generation',
  modification: 'modification',
}

export interface CatalogParams {
  page: number
  sort: string
  priceMin: number | null
  priceMax: number | null
  manufacturers: string[]
  productBrands: string[]
  inStock: boolean
  onOrder: boolean
  isOriginal: boolean
  /** Каскад подбора техники. */
  vehicleType: VehicleKind | null
  vehicleClass: string | null
  brand: string | null
  model: string | null
  generation: string | null
  modification: string | null
  /** Одношаговый подбор «как в гараже» — бэк сам разворачивает его в цепочку. */
  garageVehicleId: number | null
  tireWheel: Partial<Record<TireWheelKey, string>>
  /** Динамические атрибутные фильтры категории: `attr_<code>` → выбранные значения. */
  attributes: Record<string, string[]>
}

function parseList(value: string | null): string[] {
  return value ? value.split(',').filter(Boolean) : []
}

export function useCatalogParams() {
  const [searchParams, setSearchParams] = useSearchParams()

  const params = useMemo<CatalogParams>(() => {
    const vehicleType = (searchParams.get('vehicle_type') as VehicleKind | null) ?? null
    const classParam = vehicleType ? CLASS_PARAM[vehicleType] : null

    const tireWheel: Partial<Record<TireWheelKey, string>> = {}
    for (const key of TIRE_WHEEL_KEYS) {
      const value = searchParams.get(key)
      if (value) tireWheel[key] = value
    }

    // Атрибутные фильтры — любой параметр вида `attr_*` (§5, динамические фасеты).
    const attributes: Record<string, string[]> = {}
    for (const [key, value] of searchParams.entries()) {
      if (key.startsWith('attr_') && value) attributes[key] = parseList(value)
    }

    return {
      page: Math.max(1, Number(searchParams.get('page') ?? 1)),
      sort: searchParams.get('sort') ?? DEFAULT_SORT,
      priceMin: searchParams.get('price_min') ? Number(searchParams.get('price_min')) : null,
      priceMax: searchParams.get('price_max') ? Number(searchParams.get('price_max')) : null,
      manufacturers: parseList(searchParams.get('manufacturer')),
      productBrands: parseList(searchParams.get('product_brand')),
      inStock: searchParams.get('in_stock') === 'true',
      onOrder: searchParams.get('on_order') === 'true',
      isOriginal: searchParams.get('is_original') === 'true',
      vehicleType,
      vehicleClass: classParam ? searchParams.get(classParam) : null,
      brand: searchParams.get('brand'),
      model: searchParams.get('model'),
      generation: searchParams.get('generation'),
      modification: searchParams.get('modification'),
      garageVehicleId: searchParams.get('garage_vehicle_id')
        ? Number(searchParams.get('garage_vehicle_id'))
        : null,
      tireWheel,
      attributes,
    }
  }, [searchParams])

  const patchParams = useCallback(
    (mutate: (next: URLSearchParams) => void, options?: { keepPage?: boolean }) => {
      const next = new URLSearchParams(searchParams)
      mutate(next)
      if (!options?.keepPage) next.delete('page')
      setSearchParams(next, { preventScrollReset: true })
    },
    [searchParams, setSearchParams],
  )

  const setParam = useCallback(
    (key: string, value: string | null) => {
      patchParams((next) => {
        if (value === null || value === '') next.delete(key)
        else next.set(key, value)
      })
    },
    [patchParams],
  )

  const setList = useCallback(
    (key: string, values: string[]) => setParam(key, values.length > 0 ? values.join(',') : null),
    [setParam],
  )

  const toggleInList = useCallback(
    (key: string, value: string) => {
      const current = parseList(searchParams.get(key))
      const next = current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
      setList(key, next)
    },
    [searchParams, setList],
  )

  const setPage = useCallback(
    (page: number) => {
      patchParams(
        (next) => {
          if (page > 1) next.set('page', String(page))
          else next.delete('page')
        },
        { keepPage: true },
      )
    },
    [patchParams],
  )

  /**
   * Подбор техники. Ни один шаг не блокирует остальные: выбрать можно
   * любой уровень первым, а `patch` доносит известных предков.
   * Сбрасывается только то, что лежит НИЖЕ изменённого уровня.
   */
  const applyVehicle = useCallback(
    (patch: Partial<VehicleSelection>, level: VehicleLevel) => {
      patchParams((next) => {
        const clearClass = () => {
          for (const key of Object.values(CLASS_PARAM)) next.delete(key)
        }

        // Сначала чистим всё, что ниже изменённого уровня.
        for (const lower of VEHICLE_LEVELS.slice(VEHICLE_LEVELS.indexOf(level) + 1)) {
          if (lower === 'vehicleClass') clearClass()
          else next.delete(VEHICLE_PARAM[lower])
        }

        const type = patch.vehicleType ?? ((next.get('vehicle_type') as VehicleKind | null) ?? null)

        if ('vehicleType' in patch) {
          if (patch.vehicleType) next.set('vehicle_type', patch.vehicleType)
          else next.delete('vehicle_type')
        }
        if ('vehicleClass' in patch) {
          clearClass()
          if (type && patch.vehicleClass) next.set(CLASS_PARAM[type], patch.vehicleClass)
        }
        for (const key of ['brand', 'model', 'generation', 'modification'] as const) {
          if (!(key in patch)) continue
          const value = patch[key]
          if (value) next.set(key, value)
          else next.delete(key)
        }
      })
    },
    [patchParams],
  )

  const resetVehicle = useCallback(() => applyVehicle({ vehicleType: null }, 'vehicleType'), [applyVehicle])

  const reset = useCallback(() => {
    setSearchParams(new URLSearchParams(), { preventScrollReset: true })
  }, [setSearchParams])

  const vehicleDepth =
    (params.vehicleType ? 1 : 0) +
    (params.vehicleClass ? 1 : 0) +
    (params.brand ? 1 : 0) +
    (params.model ? 1 : 0) +
    (params.generation ? 1 : 0) +
    (params.modification ? 1 : 0)

  const activeCount =
    (params.priceMin || params.priceMax ? 1 : 0) +
    params.manufacturers.length +
    params.productBrands.length +
    (params.inStock ? 1 : 0) +
    (params.onOrder ? 1 : 0) +
    (params.isOriginal ? 1 : 0) +
    Object.keys(params.tireWheel).length +
    Object.values(params.attributes).reduce((sum, values) => sum + values.length, 0) +
    (params.garageVehicleId ? 1 : 0) +
    vehicleDepth

  /** То, что уходит в запрос списка товаров — уже в терминах бэкенда. */
  const queryParams = useMemo(() => {
    const out: Record<string, string | number | boolean> = {
      page: params.page,
      page_size: PAGE_SIZE,
      sort: params.sort,
    }
    if (params.priceMin) out['price_min'] = params.priceMin
    if (params.priceMax) out['price_max'] = params.priceMax
    if (params.manufacturers.length) out['manufacturer'] = params.manufacturers.join(',')
    if (params.productBrands.length) out['product_brand'] = params.productBrands.join(',')
    if (params.inStock) out['in_stock'] = true
    if (params.onOrder) out['on_order'] = true
    if (params.isOriginal) out['is_original'] = true
    if (params.vehicleType) out['vehicle_type'] = params.vehicleType
    if (params.vehicleType && params.vehicleClass) out[CLASS_PARAM[params.vehicleType]] = params.vehicleClass
    if (params.brand) out['brand'] = params.brand
    if (params.model) out['model'] = params.model
    if (params.generation) out['generation'] = params.generation
    if (params.modification) out['modification'] = params.modification
    if (params.garageVehicleId) out['garage_vehicle_id'] = params.garageVehicleId
    for (const [key, value] of Object.entries(params.tireWheel)) {
      if (value) out[key] = value
    }
    for (const [code, values] of Object.entries(params.attributes)) {
      if (values.length) out[code] = values.join(',')
    }
    return out
  }, [params])

  return {
    params,
    setParam,
    setList,
    toggleInList,
    setPage,
    applyVehicle,
    resetVehicle,
    reset,
    activeCount,
    vehicleDepth,
    queryParams,
  }
}
