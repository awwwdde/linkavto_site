import { useParams } from 'react-router'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, PageMeta } from '@/shared/ui'

export function Component() {
  const { orderId } = useParams()

  return (
    <>
      <PageMeta title="Оплата не прошла — LINKAVTO" canonicalPath={`/checkout/fail/${orderId}`} noIndex />
      <Container className="py-12">
        <EmptyState
          title={t('checkout.failTitle')}
          text={t('checkout.failText')}
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <ButtonLink to="/checkout" variant="primary">
                {t('checkout.retryPay')}
              </ButtonLink>
              <ButtonLink to="/profile/orders">{t('checkout.toOrders')}</ButtonLink>
              <ButtonLink to="/">{t('common.toHome')}</ButtonLink>
            </div>
          }
        />
      </Container>
    </>
  )
}
