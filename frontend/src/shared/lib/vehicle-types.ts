import type { VehicleType } from '@/shared/api/types'

/**
 * Мета типа транспорта (§3, §3.4).
 *
 * ВАЖНО: цветового кодирования категорий НЕТ (отменено сознательно в §3).
 * Все типы техники монохромны; характер даёт типографика и сетка, а не цвет.
 * Классы ниже сознательно нейтральны — иконки на нейтральном `--color-icon`,
 * подложки на `--color-ink`, среда на `--color-paper` (§3.4 правило среды).
 * Поля сохранены, чтобы потребители (CategoryTile, GarageChip) не переписывались.
 */
export interface VehicleTypeMeta {
  type: VehicleType
  /** Канонический слаг корневого раздела каталога: `/category/{slug}`. */
  slug: string
  /** Цвет иконки/названия — нейтральный (§3.1). */
  text: string
  /** Подложка плитки — нейтральная, без цветного фона (§3.1). */
  tile: string
  /** Тёмная заливка (акценты-паузы) — монохром (§3.4). */
  bg: string
  /** Среда экрана — всегда бумага, без тонирования по категории (§3.4). */
  env: string
}

const NEUTRAL = {
  text: 'text-icon',
  tile: 'bg-ink/5',
  bg: 'bg-ink',
  env: 'bg-paper',
} as const

/** Корневой раздел каталога для типа техники (обратно к `SLUG_TO_TYPE`). */
const TYPE_TO_SLUG: Record<VehicleType, string> = {
  car: 'legkovye',
  truck: 'gruzovye',
  moto: 'moto',
  special: 'spectehnika',
  tires: 'shiny-i-diski',
  service: 'dlya-to',
}

function metaFor(type: VehicleType): VehicleTypeMeta {
  return { type, slug: TYPE_TO_SLUG[type], ...NEUTRAL }
}

const TYPES: VehicleType[] = ['car', 'truck', 'moto', 'special', 'tires', 'service']

const META = Object.fromEntries(TYPES.map((type) => [type, metaFor(type)])) as Record<
  VehicleType,
  VehicleTypeMeta
>

/** Корневые слаги категорий (мок + show_in) → тип транспорта. */
const SLUG_TO_TYPE: Record<string, VehicleType> = {
  car: 'car',
  cars: 'car',
  legkovye: 'car',
  truck: 'truck',
  trucks: 'truck',
  gruzovye: 'truck',
  moto: 'moto',
  special: 'special',
  spectehnika: 'special',
  tires: 'tires',
  'shiny-i-diski': 'tires',
  service: 'service',
  'dlya-to': 'service',
}

export function vehicleMeta(type: VehicleType | null | undefined): VehicleTypeMeta | null {
  if (!type) return null
  return META[type] ?? null
}

/** Мета по пути/слагу категории (`legkovye/...` или `car`). */
export function vehicleMetaBySlug(pathOrSlug: string | null | undefined): VehicleTypeMeta | null {
  if (!pathOrSlug) return null
  const root = pathOrSlug.split('/').filter(Boolean)[0]
  if (!root) return null
  const type = SLUG_TO_TYPE[root]
  return type ? META[type] : null
}
