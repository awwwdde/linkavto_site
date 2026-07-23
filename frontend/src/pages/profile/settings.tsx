import { t } from '@/shared/i18n'
import { Input } from '@/shared/ui'
import { useAuthStore } from '@/features/auth/store'

export function Component() {
  const user = useAuthStore((state) => state.user)

  return (
    <section className="flex max-w-[480px] flex-col gap-4 rounded-card bg-surface p-4 shadow-float lg:p-6">
      <h2 className="text-md font-semibold">{t('profile.settings')}</h2>
      <Input label={t('auth.emailLabel')} value={user?.email ?? ''} readOnly />
      <Input label={t('checkout.name')} defaultValue={user?.name ?? ''} placeholder="Имя и фамилия" />
    </section>
  )
}
