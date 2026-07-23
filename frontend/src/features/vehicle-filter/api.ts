import { get } from '@/shared/api/client'
import type {
  VehicleBrandOption,
  VehicleClassOption,
  VehicleGenerationOption,
  VehicleKind,
  VehicleModelOption,
  VehicleModificationOption,
} from '@/shared/api/types'

/**
 * TODO(api): этих ручек нет в контракте §7 — они выведены из моделей Django
 * (CarType/CarBrand/CarModel/CarGeneration/CarModification и аналоги).
 * Имена GET-параметров совпадают с shop/views.py.
 *
 * Родитель во всех запросах необязателен: без него ручка отдаёт полный список,
 * поэтому любой шаг подбора можно выбрать первым.
 */

function params(entries: Record<string, string | null | undefined>) {
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(entries)) {
    if (value) out[key] = value
  }
  return out
}

export const fetchVehicleClasses = (vehicleType: VehicleKind | null) =>
  get<VehicleClassOption[]>('catalog/vehicle-classes/', params({ vehicle_type: vehicleType }))

export const fetchVehicleBrands = (vehicleType: VehicleKind | null, classSlug: string | null) =>
  get<VehicleBrandOption[]>('catalog/brands/', params({ vehicle_type: vehicleType, class: classSlug }))

export const fetchVehicleModels = (vehicleType: VehicleKind | null, brandSlug: string | null) =>
  get<VehicleModelOption[]>('catalog/models/', params({ vehicle_type: vehicleType, brand: brandSlug }))

export const fetchVehicleGenerations = (vehicleType: VehicleKind | null, modelSlug: string | null) =>
  get<VehicleGenerationOption[]>('catalog/generations/', params({ vehicle_type: vehicleType, model: modelSlug }))

export const fetchVehicleModifications = (vehicleType: VehicleKind | null, generationSlug: string | null) =>
  get<VehicleModificationOption[]>(
    'catalog/modifications/',
    params({ vehicle_type: vehicleType, generation: generationSlug }),
  )
