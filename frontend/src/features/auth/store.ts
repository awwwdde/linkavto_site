import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser } from '@/shared/api/types'

interface AuthState {
  user: AuthUser | null
  token: string | null
  signIn: (user: AuthUser, token: string) => void
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
      signOut: () => {
        localStorage.removeItem('linkavto:token')
        set({ user: null, token: null })
      },
    }),
    { name: 'linkavto:auth', version: 1 },
  ),
)

export const useIsAuthenticated = () => useAuthStore((state) => state.user !== null)
