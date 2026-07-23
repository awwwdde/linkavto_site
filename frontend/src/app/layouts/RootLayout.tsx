import { Outlet, useLocation } from 'react-router'
import { cn } from '@/shared/lib/cn'
import { ToastViewport } from '@/shared/ui'
import { vehicleMeta, vehicleMetaBySlug } from '@/shared/lib/vehicle-types'
import { useActiveVehicle } from '@/features/garage/store'
import { AuthModal } from '@/features/auth/AuthModal'
import { ScrollToTop } from '@/app/providers/ScrollToTop'
import { SmoothScrollProvider } from '@/app/providers/SmoothScrollProvider'
import { CatalogMenu } from './CatalogMenu'
import { SearchOverlay } from './SearchOverlay'
import { Header } from './Header'
import { TabBar } from './TabBar'
import { Footer } from './Footer'

/**
 * §3.4, правило среды: фон экрана — тонированная среда,
 * контент — белые карточки, парящие в ней.
 */
function useEnvironmentClass(): string {
  const { pathname } = useLocation()
  const activeVehicle = useActiveVehicle()

  const categoryMatch = pathname.startsWith('/category/') ? pathname.replace('/category/', '') : null
  const byCategory = vehicleMetaBySlug(categoryMatch)
  if (byCategory) return byCategory.env

  if (pathname.startsWith('/garage')) {
    return vehicleMeta(activeVehicle?.vehicle_type)?.env ?? 'bg-env'
  }

  return 'bg-env'
}

export function RootLayout() {
  const envClass = useEnvironmentClass()

  return (
    <div className={cn('flex min-h-dvh flex-col transition-colors duration-[--duration-base]', envClass)}>
      <ScrollToTop />
      <SmoothScrollProvider />
      <Header />

      <main className="flex-1 pb-24 lg:pb-0">
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
