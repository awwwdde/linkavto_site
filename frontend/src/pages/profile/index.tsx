import { useEffect } from 'react'
import { Outlet } from 'react-router'
import { t } from '@/shared/i18n'
import { Button, Container, EmptyState, PageMeta, TabsNav } from '@/shared/ui'
import { useAuthStore } from '@/features/auth/store'
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
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-xl font-semibold lg:text-2xl">{t('profile.title')}</h1>
          {user ? (
            <Button variant="ghost" onClick={signOut}>
              {t('nav.logout')}
            </Button>
          ) : null}
        </div>

        {user ? (
          <>
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
