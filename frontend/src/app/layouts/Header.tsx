import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { AnimatePresence, motion } from 'motion/react'
import { t } from '@/shared/i18n'
import { usePrefersReducedMotion } from '@/shared/lib/media'
import { Container } from '@/shared/ui/Layout'
import { Avatar } from '@/shared/ui/Avatar'
import { IconCart, IconCatalog, IconGarage, IconHeart, IconSearch, IconUser } from '@/shared/ui/Icon'
import { SmartSearch } from '@/features/search/SmartSearch'
import { useCartCount } from '@/features/cart/store'
import { useAuthStore, userDisplayName } from '@/features/auth/store'
import { useUiStore } from '@/app/ui-store'
import { AddressPill } from './AddressPill'

/** §11: разворот поиска — spring без баунса, ~0.25с; reduced-motion → мгновенно. */
const SPRING = { type: 'spring', duration: 0.25, bounce: 0 } as const

function Logo() {
  return (
    <Link
      to="/"
      className="shrink-0 font-display text-lg tracking-tight text-ink"
      aria-label={t('brand.name')}
    >
      LINKAVTO
    </Link>
  )
}

/** Иконка корзины со счётчиком; счётчик пружинит при изменении (§11). */
function CartLink() {
  const count = useCartCount()
  const reduced = usePrefersReducedMotion()
  return (
    <Link
      to="/cart"
      aria-label={t('nav.cart')}
      className="relative flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5"
    >
      <IconCart />
      {count > 0 ? (
        <motion.span
          key={reduced ? undefined : count}
          initial={reduced ? false : { scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 600, damping: 18 }}
          className="absolute -top-0.5 -right-0.5 flex h-5 min-w-5 items-center justify-center rounded-pill bg-accent px-1 text-xs font-medium text-white tabular-nums"
        >
          {count}
        </motion.span>
      ) : null}
    </Link>
  )
}

/** §4а/§7: гараж — только для авторизованного; гость видит модалку входа. */
function GarageButton({ className }: { className?: string }) {
  const user = useAuthStore((state) => state.user)
  const openAuth = useUiStore((state) => state.openAuth)
  const navigate = useNavigate()
  return (
    <button
      type="button"
      aria-label={t('nav.garage')}
      onClick={() => (user ? navigate('/garage') : openAuth('/garage'))}
      className={className}
    >
      <IconGarage />
    </button>
  )
}

/** §4а: тёмная пилюля «Войти» — вне основной пилюли, справа. После входа — профиль. */
function LoginPill() {
  const openAuth = useUiStore((state) => state.openAuth)
  const user = useAuthStore((state) => state.user)

  if (user) {
    return (
      <Link
        to="/profile"
        aria-label={t('nav.profile')}
        className="flex h-14 shrink-0 items-center gap-2 rounded-pill bg-ink px-4 text-base font-medium text-white shadow-float transition-colors duration-[--duration-fast] hover:bg-ink/90"
      >
        {user.avatar ? (
          <Avatar src={user.avatar} name={userDisplayName(user)} size={24} />
        ) : (
          <IconUser width={18} height={18} />
        )}
        <span className="max-w-[12ch] truncate">{userDisplayName(user)}</span>
      </Link>
    )
  }

  return (
    <button
      type="button"
      onClick={() => openAuth()}
      className="flex h-14 shrink-0 items-center gap-2 rounded-pill bg-ink px-5 text-base font-medium text-white shadow-float transition-colors duration-[--duration-fast] hover:bg-ink/90"
    >
      <IconUser width={18} height={18} />
      {t('nav.login')}
    </button>
  )
}

/** Свёрнутая капсула поиска — компактная, справа внутри основной пилюли (§4а). */
function CollapsedSearch({ onOpen }: { onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={t('nav.openSearch')}
      className="flex h-10 w-44 items-center gap-2 rounded-pill bg-ink/5 px-3.5 text-sm text-ink-muted transition-colors duration-[--duration-fast] hover:bg-ink/[0.08]"
    >
      <IconSearch width={16} height={16} className="shrink-0" />
      <span className="truncate">{t('search.short')}</span>
    </button>
  )
}

/** §4а, десктоп: широкая плавающая шапка поверх баннера. */
function DesktopHeader() {
  const [searchOpen, setSearchOpen] = useState(false)
  const openCatalog = useUiStore((state) => state.openCatalogMenu)

  useEffect(() => {
    if (!searchOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSearchOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [searchOpen])

  return (
    <div className="hidden lg:block">
      {/* Затемнение фона при раскрытом поиске (§4а). */}
      <AnimatePresence>
        {searchOpen ? (
          <motion.button
            type="button"
            aria-label={t('nav.close')}
            onClick={() => setSearchOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-30 cursor-default bg-ink/45 backdrop-blur-[2px]"
          />
        ) : null}
      </AnimatePresence>

      <Container>
        <div className="flex items-center gap-3 py-4">
          {/* 1. Пилюля адреса — отдельно слева (§4а). */}
          <AddressPill />

          {/* 2. Основная пилюля — компактная, по центру; при поиске превращается
              в отдельное поле + панель подсказок (§4а, два прямоугольника). */}
          <div className="flex flex-1 justify-center">
            {searchOpen ? (
              <motion.div
                key="search"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={SPRING}
                className="relative z-40 w-full [&_form]:shadow-lift"
              >
                <SmartSearch
                  autoFocus
                  variant="inline"
                  showGarageChip={false}
                  onNavigate={() => setSearchOpen(false)}
                />
              </motion.div>
            ) : (
              <div className="glass-chrome relative z-40 flex h-14 w-auto items-center gap-4 rounded-pill border border-line px-5 shadow-float">
                <Logo />
                <button
                  type="button"
                  onClick={openCatalog}
                  aria-label={t('nav.catalog')}
                  className="flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5"
                >
                  <IconCatalog />
                </button>
                <CollapsedSearch onOpen={() => setSearchOpen(true)} />
                <GarageButton className="flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5" />
              </div>
            )}
          </div>

          {/* 3. Пилюля избранное + корзина — отдельно (§4а). */}
          <div className="glass-chrome flex h-14 items-center gap-1 rounded-pill border border-line px-3 shadow-float">
            <Link
              to="/favorites"
              aria-label={t('nav.favorites')}
              className="flex h-10 w-10 items-center justify-center rounded-control text-ink transition-colors duration-[--duration-fast] hover:bg-ink/5"
            >
              <IconHeart />
            </Link>
            <CartLink />
          </div>

          {/* 4. Тёмная пилюля «Войти» (§4а). */}
          <LoginPill />
        </div>
      </Container>
    </div>
  )
}

/** Mobile: компактная шапка; навигация — в таб-баре, поиск — полноэкранный оверлей. */
function MobileHeader() {
  const openSearch = useUiStore((state) => state.openSearchOverlay)

  return (
    <div className="lg:hidden">
      <div className="glass-chrome flex h-14 items-center gap-3 border-b border-line px-4">
        <Logo />
        <button
          type="button"
          onClick={openSearch}
          aria-label={t('nav.openSearch')}
          className="flex h-10 min-w-0 flex-1 items-center gap-2 rounded-pill bg-ink/5 px-4 text-base text-ink-muted"
        >
          <IconSearch width={18} height={18} className="shrink-0" />
          <span className="truncate">{t('search.placeholderShort')}</span>
        </button>
        <CartLink />
      </div>
    </div>
  )
}

/**
 * §4а: шапка плавает поверх контента (fixed), баннер главной продолжается под ней.
 * Отступ под шапку задаёт RootLayout (main), кроме главной, где баннер уходит под неё.
 */
export function Header() {
  return (
    <header className="fixed inset-x-0 top-0 z-40">
      <DesktopHeader />
      <MobileHeader />
    </header>
  )
}
