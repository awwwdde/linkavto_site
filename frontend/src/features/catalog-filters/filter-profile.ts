import type { VehicleKind, VehicleType } from '@/shared/api/types'

/**
 * Режим каскада «подбор по автомобилю» в панели фильтров:
 * - `locked`   — раздел уже задаёт тип техники (Легковые/Грузовые/Мото/Спец),
 *                чипы типа скрыты, списки марок/классов сужены до этого типа;
 * - `optional` — тип техники не главный (шины, масла/ТО): каскад свёрнут под
 *                кнопку, главные оси — размер/спецификация из фасетов бэка;
 * - `full`     — универсальный раздел: полный каскад с выбором типа (как раньше).
 */
export type VehicleFilterMode = 'locked' | 'optional' | 'full'

export interface FilterProfile {
  vehicleMode: VehicleFilterMode
  /** Тип техники, к которому привязан раздел (только для `locked`). */
  lockedKind: VehicleKind | null
}

const LOCKED_KINDS = new Set<VehicleType>(['car', 'truck', 'moto', 'special'])

/**
 * Профиль фильтров выводится из `category.vehicle_type` — того же поля,
 * по которому бэк решает, какие фасеты (`tire_wheel`, `attributes`) прислать.
 * Единый источник правды: раздел диктует и набор фасетов, и режим каскада.
 */
export function filterProfile(vehicleType: VehicleType | null | undefined): FilterProfile {
  if (vehicleType && LOCKED_KINDS.has(vehicleType)) {
    return { vehicleMode: 'locked', lockedKind: vehicleType as VehicleKind }
  }
  // tires / service — профильные оси главные, авто-подбор вторичен.
  if (vehicleType === 'tires' || vehicleType === 'service') {
    return { vehicleMode: 'optional', lockedKind: null }
  }
  return { vehicleMode: 'full', lockedKind: null }
}
