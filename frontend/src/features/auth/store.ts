import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser } from '@/shared/api/types'
import { useGarageStore } from '@/features/garage/store'
import { useAddressStore } from '@/features/address/store'

interface AuthState {
  user: AuthUser | null
  token: string | null
  signIn: (user: AuthUser, token: string) => void
  /** Точечное обновление профиля после PATCH /account. */
  updateUser: (patch: Partial<AuthUser>) => void
  signOut: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      signIn: (user, token) => {
        localStorage.setItem('linkavto:token', token)
        set({ user, token })
      },
      updateUser: (patch) =>
        set((state) => ({ user: state.user ? { ...state.user, ...patch } : state.user })),
      signOut: () => {
        localStorage.removeItem('linkavto:token')
        set({ user: null, token: null })
        // Гараж и адреса привязаны к аккаунту — очищаем при выходе,
        // иначе авто и его каталог-контекст остаются у гостя.
        useGarageStore.getState().reset()
        useAddressStore.getState().reset()
      },
    }),
    { name: 'linkavto:auth', version: 2 },
  ),
)

export const useIsAuthenticated = () => useAuthStore((state) => state.user !== null)

/** Отображаемое имя: «Имя Фамилия» или e-mail, если имя ещё не заполнено. */
export function userDisplayName(user: AuthUser | null): string {
  if (!user) return ''
  const full = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return full || user.email
}
