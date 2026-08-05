import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { GarageVehicle } from '@/shared/api/types'

interface GarageState {
  vehicles: GarageVehicle[]
  activeVehicleId: number | null
  /** true, пока гараж живёт только локально (гость) и не смержен с бэком. */
  dirty: boolean
  setVehicles: (vehicles: GarageVehicle[]) => void
  addVehicle: (vehicle: GarageVehicle) => void
  removeVehicle: (id: number) => void
  setActive: (id: number | null) => void
  markSynced: () => void
  /** Полный сброс — при выходе из аккаунта (гараж привязан к аккаунту). */
  reset: () => void
}

/**
 * §7: гараж — сквозной контекст. Гость хранит его локально,
 * при логине список мержится на бэк.
 */
export const useGarageStore = create<GarageState>()(
  persist(
    (set) => ({
      vehicles: [],
      activeVehicleId: null,
      dirty: false,

      setVehicles: (vehicles) =>
        set((state) => ({
          vehicles,
          activeVehicleId:
            state.activeVehicleId && vehicles.some((v) => v.id === state.activeVehicleId)
              ? state.activeVehicleId
              : (vehicles[0]?.id ?? null),
          dirty: false,
        })),

      addVehicle: (vehicle) =>
        set((state) => ({
          vehicles: state.vehicles.some((v) => v.id === vehicle.id) ? state.vehicles : [...state.vehicles, vehicle],
          activeVehicleId: vehicle.id,
          dirty: true,
        })),

      removeVehicle: (id) =>
        set((state) => {
          const vehicles = state.vehicles.filter((v) => v.id !== id)
          return {
            vehicles,
            activeVehicleId: state.activeVehicleId === id ? (vehicles[0]?.id ?? null) : state.activeVehicleId,
            dirty: true,
          }
        }),

      setActive: (id) => set({ activeVehicleId: id }),
      markSynced: () => set({ dirty: false }),
      reset: () => set({ vehicles: [], activeVehicleId: null, dirty: false }),
    }),
    { name: 'linkavto:garage', version: 1 },
  ),
)

export function useActiveVehicle(): GarageVehicle | null {
  return useGarageStore((state) => state.vehicles.find((v) => v.id === state.activeVehicleId) ?? null)
}
