import { useRouteError } from 'react-router'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, ErrorState } from '@/shared/ui'

/** Единая граница ошибок роутера: текст + действие, без стектрейсов в проде. */
export function RouteError() {
  const error = useRouteError()

  if (import.meta.env.DEV) {
    console.error(error)
  }

  return (
    <Container className="py-12">
      <ErrorState
        title={t('common.errorTitle')}
        text={t('common.errorText')}
      />
      <div className="mt-4 flex justify-center">
        <ButtonLink to="/" variant="secondary">
          {t('common.toHome')}
        </ButtonLink>
      </div>
    </Container>
  )
}
