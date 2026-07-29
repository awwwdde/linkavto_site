import { useEffect } from 'react'
import { Link, Outlet } from 'react-router'
import { t } from '@/shared/i18n'
import { Avatar, Button, Container, EmptyState, PageMeta, TabsNav } from '@/shared/ui'
import { useAuthStore, userDisplayName } from '@/features/auth/store'
import { useUiStore } from '@/app/ui-store'

export function Component() {
  const user = useAuthStore((state) => state.user)
  const signOut = useAuthStore((state) => state.signOut)
  const openAuth = useUiStore((state) => state.openAuth)

  useEffect(() => {
    if (!user) openAuth('/profile')
  }, [user, openAuth])

  return (
    <>
      <PageMeta title="Профиль — LINKAVTO" canonicalPath="/profile" noIndex />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        {user ? (
          <>
            {/* Шапка профиля: аватар + имя + контакты. */}
            <div className="flex items-center gap-4 rounded-card bg-surface p-4 shadow-float lg:p-6">
              <Avatar src={user.avatar} name={userDisplayName(user)} size={64} />
              <div className="min-w-0 flex-1">
                <h1 className="truncate text-xl font-semibold">{userDisplayName(user)}</h1>
                <p className="truncate text-sm text-ink-muted">
                  {user.email}
                  {user.phone ? ` · ${user.phone}` : ''}
                </p>
              </div>
              <Button variant="ghost" onClick={signOut}>
                {t('nav.logout')}
              </Button>
            </div>

            {!user.profile_completed ? (
              <Link
                to="/profile/settings"
                className="rounded-card border border-dashed border-line bg-surface px-4 py-3 text-sm text-ink-muted transition-colors duration-[--duration-fast] hover:border-ink-muted hover:text-ink"
              >
                {t('profile.completePrompt')}
              </Link>
            ) : null}

            <TabsNav
              items={[
                { to: '/profile/orders', label: t('profile.orders') },
                { to: '/profile/addresses', label: t('profile.addresses') },
                { to: '/profile/settings', label: t('profile.settings') },
              ]}
            />
            <Outlet />
          </>
        ) : (
          <EmptyState
            title={t('auth.title')}
            text="Войдите по коду из письма — заказы и адреса подтянутся автоматически."
            action={
              <Button variant="primary" onClick={() => openAuth('/profile')}>
                {t('nav.login')}
              </Button>
            }
          />
        )}
      </Container>
    </>
  )
}
