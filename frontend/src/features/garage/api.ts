import { del, get, post } from '@/shared/api/client'
import type { GarageOption, GarageVehicle, VehicleType } from '@/shared/api/types'

export const fetchGarageVehicles = () => get<GarageVehicle[]>('garage/vehicles/')

export interface CreateVehiclePayload {
  vehicle_type?: VehicleType
  make_id?: number
  model_id?: number
  modification_id?: number
  vin?: string
}

export const createGarageVehicle = (payload: CreateVehiclePayload) =>
  post<GarageVehicle>('garage/vehicles/', payload)

export const deleteGarageVehicle = (id: number) => del<void>(`garage/vehicles/${id}/`)

export const fetchMakes = (vehicleType: VehicleType) => get<GarageOption[]>('garage/makes/', { type: vehicleType })

export const fetchModels = (makeId: number) => get<GarageOption[]>('garage/models/', { make: makeId })

export const fetchModifications = (modelId: number) =>
  get<GarageOption[]>('garage/modifications/', { model: modelId })
