import { t } from '@/shared/i18n'
import { ButtonLink, EmptyState } from '@/shared/ui'

export function Component() {
  return (
    <EmptyState
      title={t('profile.addressesEmptyTitle')}
      text={t('profile.addressesEmptyText')}
      action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
    />
  )
}
