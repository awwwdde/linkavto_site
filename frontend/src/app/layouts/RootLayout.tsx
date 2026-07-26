import { Outlet } from 'react-router'
import { ToastViewport } from '@/shared/ui'
import { AuthModal } from '@/features/auth/AuthModal'
import { ScrollToTop } from '@/app/providers/ScrollToTop'
import { SmoothScrollProvider } from '@/app/providers/SmoothScrollProvider'
import { CatalogMenu } from './CatalogMenu'
import { SearchOverlay } from './SearchOverlay'
import { Header } from './Header'
import { TabBar } from './TabBar'
import { Footer } from './Footer'

/**
 * §3.4, правило среды: фон экрана — --color-paper (единая среда, без тонирования
 * по категории и без градиентов), контент — белые карточки, парящие в ней.
 * §3.4, правило слоёв: ровно три уровня — среда → карточки → активный слой.
 */
export function RootLayout() {
  return (
    <div className="flex min-h-dvh flex-col bg-paper">
      <ScrollToTop />
      <SmoothScrollProvider />
      <Header />

      {/* Отступ под fixed-шапку (§4а). Главная переопределяет его, уводя баннер под шапку. */}
      <main className="flex-1 pt-14 pb-24 lg:pt-20 lg:pb-0">
        <Outlet />
      </main>

      <Footer />
      <TabBar />

      {/* Активный слой (§3.4, третий уровень глубины). */}
      <AuthModal />
      <CatalogMenu />
      <SearchOverlay />
      <ToastViewport />
    </div>
  )
}
