import { useParams } from 'react-router'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, PageMeta } from '@/shared/ui'

export function Component() {
  const { orderId } = useParams()

  return (
    <>
      <PageMeta title="Заказ оформлен — LINKAVTO" canonicalPath={`/checkout/success/${orderId}`} noIndex />
      <Container className="py-12">
        <EmptyState
          title={`${t('checkout.successTitle')} № ${orderId}`}
          text={t('checkout.successText')}
          action={
            <div className="flex flex-wrap justify-center gap-2">
              <ButtonLink to="/profile/orders" variant="primary">
                {t('checkout.toOrders')}
              </ButtonLink>
              <ButtonLink to="/">{t('common.toHome')}</ButtonLink>
            </div>
          }
        />
      </Container>
    </>
  )
}
