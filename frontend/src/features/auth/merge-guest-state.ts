import { post } from '@/shared/api/client'
import type { GarageVehicle } from '@/shared/api/types'
import { useCartStore } from '@/features/cart/store'
import { useGarageStore } from '@/features/garage/store'

/**
 * §7: гость держит корзину и гараж локально; при логине они мержатся на бэк.
 * Ошибка мержа не должна ломать вход — локальные данные остаются на месте.
 */
export async function mergeGuestState(): Promise<void> {
  const cart = useCartStore.getState()
  const garage = useGarageStore.getState()

  if (cart.items.length > 0) {
    try {
      await post('cart/merge/', {
        items: cart.items.map((item) => ({
          product_id: item.product.id,
          offer_id: item.offer?.id ?? null,
          quantity: item.quantity,
        })),
      })
      cart.clear()
    } catch {
      /* корзина остаётся локальной до следующей попытки */
    }
  }

  if (garage.dirty && garage.vehicles.length > 0) {
    try {
      const merged = await post<GarageVehicle[]>('garage/merge/', {
        vehicles: garage.vehicles.map((vehicle) => ({
          vin: vehicle.vin,
          make: vehicle.make,
          model: vehicle.model,
          modification: vehicle.modification,
        })),
      })
      garage.setVehicles(merged)
    } catch {
      /* гараж остаётся локальным до следующей попытки */
    }
  }
}
