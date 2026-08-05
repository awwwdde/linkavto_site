import { useState } from 'react'
import type { Address, DeliveryType, PickupProvider } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { Button, Checkbox, Input, Select, toast } from '@/shared/ui'
import { useAddressStore, type AddressDraft } from './store'
import { PICKUP_PROVIDERS, pickupPoints } from './pickup'

const EMPTY: AddressDraft = {
  title: '',
  delivery_type: 'courier',
  full_address: '',
  postal_code: '',
  comment: '',
  pickup_provider: null,
  pickup_point_name: null,
  is_default: false,
}

export function AddressForm({ initial, onDone }: { initial?: Address; onDone: () => void }) {
  const add = useAddressStore((s) => s.add)
  const update = useAddressStore((s) => s.update)
  const [form, setForm] = useState<AddressDraft>(initial ? { ...initial } : EMPTY)

  const set = <K extends keyof AddressDraft>(key: K, value: AddressDraft[K]) =>
    setForm((state) => ({ ...state, [key]: value }))

  const isPickup = form.delivery_type === 'pickup'
  const provider = (form.pickup_provider ?? 'cdek') as PickupProvider
  const points = pickupPoints(provider)
  const valid = isPickup ? Boolean(form.pickup_point_name) : form.full_address.trim().length > 0

  const submit = () => {
    if (!valid) return
    const draft: AddressDraft = isPickup
      ? { ...form, full_address: '', pickup_provider: provider }
      : { ...form, pickup_provider: null, pickup_point_name: null }
    if (initial) update(initial.id, draft)
    else add(draft)
    toast.ok(t('address.saved'))
    onDone()
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
    >
      {/* Способ получения */}
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-ink-muted">{t('address.deliveryType')}</span>
        <div className="grid grid-cols-2 gap-2">
          {(['courier', 'pickup'] as DeliveryType[]).map((type) => (
            <button
              key={type}
              type="button"
              aria-pressed={form.delivery_type === type}
              onClick={() => set('delivery_type', type)}
              className={cn(
                'min-h-11 rounded-control border px-3 text-sm font-medium transition-colors duration-[--duration-fast]',
                form.delivery_type === type
                  ? 'border-ink bg-ink text-white'
                  : 'border-line bg-surface text-ink hover:border-ink-muted',
              )}
            >
              {type === 'courier' ? t('address.courier') : t('address.pickup')}
            </button>
          ))}
        </div>
      </div>

      <Input
        label={t('address.label')}
        placeholder={t('address.labelPlaceholder')}
        value={form.title}
        onChange={(e) => set('title', e.target.value)}
      />

      {isPickup ? (
        <>
          <Select
            label={t('address.provider')}
            value={provider}
            onChange={(e) => {
              set('pickup_provider', e.target.value as PickupProvider)
              set('pickup_point_name', null)
            }}
          >
            {PICKUP_PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </Select>
          <Select
            label={t('address.point')}
            value={form.pickup_point_name ?? ''}
            onChange={(e) => set('pickup_point_name', e.target.value || null)}
          >
            <option value="">{t('address.pointChoose')}</option>
            {points.map((point) => (
              <option key={point} value={point}>
                {point}
              </option>
            ))}
          </Select>
          <p className="text-xs text-ink-muted">{t('address.mapHint')}</p>
        </>
      ) : (
        <>
          <Input
            label={t('address.full')}
            placeholder={t('address.fullPlaceholder')}
            value={form.full_address}
            onChange={(e) => set('full_address', e.target.value)}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label={t('address.postal')}
              inputMode="numeric"
              value={form.postal_code}
              onChange={(e) => set('postal_code', e.target.value)}
            />
          </div>
        </>
      )}

      <Input
        label={t('address.comment')}
        value={form.comment}
        onChange={(e) => set('comment', e.target.value)}
      />

      <Checkbox
        checked={form.is_default}
        onChange={(e) => set('is_default', e.target.checked)}
        label={t('address.makeDefault')}
      />

      <Button type="submit" variant="primary" size="lg" block disabled={!valid}>
        {t('address.save')}
      </Button>
    </form>
  )
}
