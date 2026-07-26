import { NavLink, useLocation } from 'react-router'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconCart, IconCatalog, IconGarage, IconHome, IconUser } from '@/shared/ui/Icon'
import { useCartCount } from '@/features/cart/store'
import { useUiStore } from '@/app/ui-store'

const ITEM =
  'flex min-h-14 flex-1 flex-col items-center justify-center gap-1 text-xs transition-colors duration-[--duration-fast]'

/** §4: mobile-каркас — нижний таб-бар, Гараж в центре и приподнят. */
export function TabBar() {
  const count = useCartCount()
  const openCatalog = useUiStore((state) => state.openCatalogMenu)
  const { pathname } = useLocation()

  const link = ({ isActive }: { isActive: boolean }) => cn(ITEM, isActive ? 'text-ink' : 'text-ink-muted')

  return (
    <nav
      aria-label={t('nav.menu')}
      className="glass-chrome fixed inset-x-0 bottom-0 z-40 flex items-stretch border-t border-line pb-[env(safe-area-inset-bottom)] lg:hidden"
    >
      <NavLink to="/" end className={link}>
        <IconHome width={22} height={22} />
        {t('nav.home')}
      </NavLink>

      <button
        type="button"
        onClick={openCatalog}
        className={cn(ITEM, pathname.startsWith('/category') ? 'text-ink' : 'text-ink-muted')}
      >
        <IconCatalog width={22} height={22} />
        {t('nav.catalog')}
      </button>

      <NavLink to="/garage" className={cn(ITEM, 'relative')}>
        {({ isActive }) => (
          <>
            <span
              className={cn(
                'absolute -top-5 flex h-12 w-12 items-center justify-center rounded-pill shadow-float',
                isActive ? 'bg-ink text-white' : 'bg-surface text-ink',
              )}
            >
              <IconGarage width={24} height={24} />
            </span>
            <span className={cn('mt-7 text-xs', isActive ? 'text-ink' : 'text-ink-muted')}>{t('nav.garage')}</span>
          </>
        )}
      </NavLink>

      <NavLink to="/cart" className={link}>
        <span className="relative">
          <IconCart width={22} height={22} />
          {count > 0 ? (
            <span className="absolute -top-1.5 -right-2 flex h-4 min-w-4 items-center justify-center rounded-pill bg-accent px-1 text-2xs font-medium text-white tabular-nums">
              {count}
            </span>
          ) : null}
        </span>
        {t('nav.cart')}
      </NavLink>

      <NavLink to="/profile" className={link}>
        <IconUser width={22} height={22} />
        {t('nav.profile')}
      </NavLink>
    </nav>
  )
}
