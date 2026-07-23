import { Link } from 'react-router'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { Container } from '@/shared/ui/Layout'
import { IconCart, IconCatalog, IconHeart, IconSearch, IconUser } from '@/shared/ui/Icon'
import { SmartSearch } from '@/features/search/SmartSearch'
import { useCartCount } from '@/features/cart/store'
import { useAuthStore } from '@/features/auth/store'
import { useUiStore } from '@/app/ui-store'

function Logo() {
  return (
    <Link to="/" className="shrink-0 font-display text-lg tracking-tight text-ink" aria-label={t('brand.name')}>
      LINKAVTO
    </Link>
  )
}

function CartLink({ compact = false }: { compact?: boolean }) {
  const count = useCartCount()
  return (
    <Link
      to="/cart"
      aria-label={t('nav.cart')}
      className="relative flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5"
    >
      <IconCart />
      {count > 0 ? (
        <span
          className="absolute -top-0.5 -right-0.5 flex h-5 min-w-5 items-center justify-center rounded-pill bg-cta px-1 text-xs font-medium text-cta-ink tabular-nums"
          aria-hidden={compact}
        >
          {count}
        </span>
      ) : null}
    </Link>
  )
}

/** Desktop-шапка: плавающая пилюля со стеклом (одно из двух разрешённых мест, §3.1). */
export function Header() {
  const openAuth = useUiStore((state) => state.openAuth)
  const openCatalog = useUiStore((state) => state.openCatalogMenu)
  const openSearch = useUiStore((state) => state.openSearchOverlay)
  const user = useAuthStore((state) => state.user)

  return (
    <header className="sticky top-0 z-40 pt-0 lg:top-4 lg:pt-4">
      <Container>
        <div
          className={cn(
            'glass-chrome flex h-16 items-center gap-3 border-b border-line px-4',
            'lg:h-16 lg:gap-4 lg:rounded-pill lg:border-0 lg:px-4 lg:shadow-float',
          )}
        >
          <Logo />

          <button
            type="button"
            onClick={openCatalog}
            className="hidden h-10 items-center gap-2 rounded-control px-3 text-base font-medium text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5 lg:flex"
          >
            <IconCatalog width={18} height={18} />
            {t('nav.catalog')}
          </button>

          {/* Полноценный поиск — только desktop; на mobile строка открывает оверлей. */}
          <div className="hidden min-w-0 flex-1 lg:block">
            <SmartSearch />
          </div>

          <button
            type="button"
            onClick={openSearch}
            className="flex h-10 min-w-0 flex-1 items-center gap-2 rounded-pill border border-line bg-surface px-4 text-base text-ink-muted lg:hidden"
          >
            <IconSearch width={18} height={18} />
            <span className="truncate">{t('search.placeholderShort')}</span>
          </button>

          <div className="flex shrink-0 items-center gap-1">
            <Link
              to="/favorites"
              aria-label={t('nav.favorites')}
              className="hidden h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5 lg:flex"
            >
              <IconHeart />
            </Link>

            <div className="hidden lg:block">
              <CartLink />
            </div>

            {user ? (
              <Link
                to="/profile"
                aria-label={t('nav.profile')}
                className="hidden h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5 lg:flex"
              >
                <IconUser />
              </Link>
            ) : (
              <button
                type="button"
                onClick={() => openAuth()}
                className="hidden h-10 items-center gap-2 rounded-control px-3 text-base font-medium text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5 lg:flex"
              >
                <IconUser width={18} height={18} />
                {t('nav.login')}
              </button>
            )}
          </div>
        </div>
      </Container>
    </header>
  )
}
