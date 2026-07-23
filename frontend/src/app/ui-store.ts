import { create } from 'zustand'

/**
 * UI-оверлеи приложения. §7: одна AuthModal на всё приложение,
 * открывается из любого места через этот стор.
 */
interface UiState {
  authModalOpen: boolean
  catalogMenuOpen: boolean
  searchOverlayOpen: boolean
  /** Куда вернуться после успешного входа. */
  authRedirectTo: string | null

  openAuth: (redirectTo?: string) => void
  closeAuth: () => void
  openCatalogMenu: () => void
  closeCatalogMenu: () => void
  openSearchOverlay: () => void
  closeSearchOverlay: () => void
}

export const useUiStore = create<UiState>((set) => ({
  authModalOpen: false,
  catalogMenuOpen: false,
  searchOverlayOpen: false,
  authRedirectTo: null,

  openAuth: (redirectTo) => set({ authModalOpen: true, authRedirectTo: redirectTo ?? null }),
  closeAuth: () => set({ authModalOpen: false }),
  openCatalogMenu: () => set({ catalogMenuOpen: true }),
  closeCatalogMenu: () => set({ catalogMenuOpen: false }),
  openSearchOverlay: () => set({ searchOverlayOpen: true }),
  closeSearchOverlay: () => set({ searchOverlayOpen: false }),
}))
