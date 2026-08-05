import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Address } from '@/shared/api/types'

export type AddressDraft = Omit<Address, 'id'>

interface AddressState {
  addresses: Address[]
  add: (draft: AddressDraft) => Address
  update: (id: number, patch: Partial<AddressDraft>) => void
  remove: (id: number) => void
  setDefault: (id: number) => void
  /** Полный сброс — при выходе из аккаунта. */
  reset: () => void
}

let seq = 1

/** Единственный дефолтный адрес: назначая один, снимаем флаг с остальных. */
function normalizeDefault(addresses: Address[], defaultId: number): Address[] {
  return addresses.map((a) => ({ ...a, is_default: a.id === defaultId }))
}

/**
 * §7: адреса покупателя. Гость хранит локально; в проде — синхронизация с
 * аккаунтом. TODO(api): CRUD `account/addresses/`.
 */
export const useAddressStore = create<AddressState>()(
  persist(
    (set) => ({
      addresses: [],

      add: (draft) => {
        const address: Address = { ...draft, id: ++seq }
        set((state) => {
          const first = state.addresses.length === 0
          const list = [...state.addresses, { ...address, is_default: draft.is_default || first }]
          return { addresses: address.is_default || first ? normalizeDefault(list, address.id) : list }
        })
        return address
      },

      update: (id, patch) =>
        set((state) => {
          let list = state.addresses.map((a) => (a.id === id ? { ...a, ...patch } : a))
          if (patch.is_default) list = normalizeDefault(list, id)
          return { addresses: list }
        }),

      remove: (id) =>
        set((state) => {
          const wasDefault = state.addresses.find((a) => a.id === id)?.is_default
          let list = state.addresses.filter((a) => a.id !== id)
          // Удалили дефолтный — назначаем первый оставшийся.
          if (wasDefault && list.length > 0) list = normalizeDefault(list, list[0]!.id)
          return { addresses: list }
        }),

      setDefault: (id) => set((state) => ({ addresses: normalizeDefault(state.addresses, id) })),

      reset: () => set({ addresses: [] }),
    }),
    {
      name: 'linkavto:addresses',
      version: 1,
      onRehydrateStorage: () => (state) => {
        // seq выше максимального id, чтобы новые адреса не конфликтовали.
        seq = Math.max(0, ...(state?.addresses.map((a) => a.id) ?? [0]))
      },
    },
  ),
)
