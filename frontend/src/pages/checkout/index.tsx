import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { post } from '@/shared/api/client'
import { ApiError } from '@/shared/api/client'
import { t } from '@/shared/i18n'
import { Button, ButtonLink, Container, EmptyState, Input, PageMeta, Price, Radio, Tabs, toast } from '@/shared/ui'
import { useCartStore } from '@/features/cart/store'
import { PaymentModal } from '@/features/checkout/PaymentModal'

const DELIVERY_PER_SELLER = 39000

const schema = z.object({
  name: z.string().min(2, 'Укажите имя и фамилию — так продавец найдёт заказ.'),
  phone: z.string().min(10, 'Телефон нужен для связи по доставке.'),
  city: z.string().min(2, 'Укажите город доставки.'),
  address: z.string().min(4, 'Укажите улицу, дом и квартиру.'),
  comment: z.string().optional(),
})
type CheckoutForm = z.infer<typeof schema>

type Step = 'address' | 'payment' | 'confirm'
type Delivery = 'cdek' | 'post' | 'pickup'
type Payment = 'card' | 'sbp' | 'cash'

export function Component() {
  const navigate = useNavigate()
  const items = useCartStore((state) => state.items)
  const clear = useCartStore((state) => state.clear)

  const [step, setStep] = useState<Step>('address')
  const [delivery, setDelivery] = useState<Delivery>('cdek')
  const [payment, setPayment] = useState<Payment>('card')
  const [pending, setPending] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  const [placedOrder, setPlacedOrder] = useState<{ id: number } | null>(null)

  const form = useForm<CheckoutForm>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', phone: '', city: '', address: '', comment: '' },
  })

  const subtotal = items.reduce((sum, item) => sum + (item.offer?.price ?? item.product.price) * item.quantity, 0)
  const sellersCount = new Set(items.map((item) => item.offer?.seller.id ?? 0)).size
  const deliveryCost = delivery === 'pickup' ? 0 : sellersCount * DELIVERY_PER_SELLER

  if (items.length === 0) {
    return (
      <Container className="py-12">
        <PageMeta title="Оформление заказа — LINKAVTO" canonicalPath="/checkout" noIndex />
        <EmptyState
          title={t('cart.emptyTitle')}
          text={t('cart.emptyText')}
          action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
        />
      </Container>
    )
  }

  const submit = async () => {
    setPending(true)
    try {
      const values = form.getValues()
      const order = await post<{ id: number; number: string }>('orders/', {
        delivery_method: delivery,
        payment_method: payment,
        items: items.map((item) => ({
          product_id: item.product.id,
          offer_id: item.offer?.id ?? null,
          quantity: item.quantity,
        })),
        ...values,
      })
      // Онлайн-оплата — через мок-эквайер; наличными — сразу успех.
      if (payment === 'cash') {
        clear()
        navigate(`/checkout/success/${order.id}`)
      } else {
        setPlacedOrder(order)
        setPayOpen(true)
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t('common.errorText'))
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <PageMeta title="Оформление заказа — LINKAVTO" canonicalPath="/checkout" noIndex />

      <Container className="flex flex-col gap-6 py-4 lg:py-8">
        <h1 className="text-xl font-semibold lg:text-2xl">{t('checkout.title')}</h1>

        <Tabs
          aria-label={t('checkout.title')}
          value={step}
          onChange={setStep}
          items={[
            { value: 'address', label: t('checkout.stepAddress') },
            { value: 'payment', label: t('checkout.stepPayment') },
            { value: 'confirm', label: t('checkout.stepConfirm') },
          ]}
        />

        <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
          <div className="flex min-w-0 flex-1 flex-col gap-4 rounded-card bg-surface p-4 shadow-float lg:p-6">
            {step === 'address' ? (
              <form
                className="flex flex-col gap-4"
                onSubmit={form.handleSubmit(() => setStep('payment'))}
              >
                <fieldset className="flex flex-col gap-2">
                  <legend className="mb-2 text-base font-semibold">{t('checkout.stepAddress')}</legend>
                  <Radio
                    name="delivery"
                    checked={delivery === 'cdek'}
                    onChange={() => setDelivery('cdek')}
                    label={t('checkout.deliveryCdek')}
                    description="Пункт выдачи или курьер, 2–5 дней"
                  />
                  <Radio
                    name="delivery"
                    checked={delivery === 'post'}
                    onChange={() => setDelivery('post')}
                    label={t('checkout.deliveryPost')}
                    description="Доставка в отделение, 5–12 дней"
                  />
                  <Radio
                    name="delivery"
                    checked={delivery === 'pickup'}
                    onChange={() => setDelivery('pickup')}
                    label={t('checkout.deliveryPickup')}
                    description="Со склада продавца, бесплатно"
                  />
                </fieldset>

                <Input label={t('checkout.name')} autoComplete="name" error={form.formState.errors.name?.message} {...form.register('name')} />
                <Input
                  label={t('checkout.phone')}
                  type="tel"
                  autoComplete="tel"
                  placeholder="+7 900 000-00-00"
                  error={form.formState.errors.phone?.message}
                  {...form.register('phone')}
                />
                <Input label={t('checkout.city')} autoComplete="address-level2" error={form.formState.errors.city?.message} {...form.register('city')} />
                <Input label={t('checkout.address')} autoComplete="street-address" error={form.formState.errors.address?.message} {...form.register('address')} />
                <Input label={t('checkout.comment')} {...form.register('comment')} />

                <Button type="submit" variant="primary" size="lg" block>
                  {t('checkout.next')}
                </Button>
              </form>
            ) : step === 'payment' ? (
              <div className="flex flex-col gap-4">
                <fieldset className="flex flex-col gap-2">
                  <legend className="mb-2 text-base font-semibold">{t('checkout.stepPayment')}</legend>
                  <Radio
                    name="payment"
                    checked={payment === 'card'}
                    onChange={() => setPayment('card')}
                    label={t('checkout.payCard')}
                    description="Оплата на защищённой странице банка"
                  />
                  <Radio
                    name="payment"
                    checked={payment === 'sbp'}
                    onChange={() => setPayment('sbp')}
                    label={t('checkout.paySbp')}
                    description="По QR-коду через приложение банка"
                  />
                  <Radio
                    name="payment"
                    checked={payment === 'cash'}
                    onChange={() => setPayment('cash')}
                    label={t('checkout.payCash')}
                    description="Наличными или картой курьеру"
                  />
                </fieldset>
                <Button variant="primary" size="lg" block onClick={() => setStep('confirm')}>
                  {t('checkout.next')}
                </Button>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <h2 className="text-base font-semibold">{t('checkout.stepConfirm')}</h2>
                <dl className="flex flex-col gap-2 text-base">
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-muted">{t('checkout.name')}</dt>
                    <dd>{form.getValues('name')}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-muted">{t('checkout.phone')}</dt>
                    <dd className="tabular-nums">{form.getValues('phone')}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-muted">{t('checkout.stepAddress')}</dt>
                    <dd className="text-right">
                      {delivery === 'pickup'
                        ? t('checkout.deliveryPickup')
                        : `${form.getValues('city')}, ${form.getValues('address')}`}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-muted">{t('checkout.stepPayment')}</dt>
                    <dd>
                      {payment === 'card'
                        ? t('checkout.payCard')
                        : payment === 'sbp'
                          ? t('checkout.paySbp')
                          : t('checkout.payCash')}
                    </dd>
                  </div>
                </dl>
                <Button variant="primary" size="lg" block loading={pending} onClick={() => void submit()}>
                  {t('checkout.submit')}
                </Button>
              </div>
            )}
          </div>

          <aside className="w-full shrink-0 lg:sticky lg:top-28 lg:w-80">
            <div className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float">
              <div className="flex justify-between text-base">
                <span className="text-ink-muted">{t('cart.subtotal')}</span>
                <Price value={subtotal} size="sm" />
              </div>
              <div className="flex justify-between text-base">
                <span className="text-ink-muted">{t('cart.delivery')}</span>
                <Price value={deliveryCost} size="sm" />
              </div>
              <div className="flex items-baseline justify-between border-t border-line pt-3">
                <span className="text-md font-semibold">{t('cart.total')}</span>
                <Price value={subtotal + deliveryCost} size="lg" />
              </div>
            </div>
          </aside>
        </div>
      </Container>

      <PaymentModal
        open={payOpen}
        method={payment === 'sbp' ? 'sbp' : 'card'}
        amount={subtotal + deliveryCost}
        onSuccess={() => {
          clear()
          if (placedOrder) navigate(`/checkout/success/${placedOrder.id}`)
        }}
        onFail={() => {
          setPayOpen(false)
          if (placedOrder) navigate(`/checkout/fail/${placedOrder.id}`)
        }}
        onClose={() => setPayOpen(false)}
      />
    </>
  )
}
