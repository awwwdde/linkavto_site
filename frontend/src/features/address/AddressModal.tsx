import { useEffect, useState } from 'react'
import type { Address } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { Badge, Button, Modal } from '@/shared/ui'
import { IconPlus } from '@/shared/ui/Icon'
import { useAddressStore } from './store'
import { AddressForm } from './AddressForm'
import { PROVIDER_LABEL } from './pickup'

export function addressLabel(a: Address): string {
  if (a.delivery_type === 'pickup') {
    return [a.pickup_provider ? PROVIDER_LABEL[a.pickup_provider] : null, a.pickup_point_name].filter(Boolean).join(' · ')
  }
  return a.title ? `${a.title}: ${a.full_address}` : a.full_address
}

/** Быстрый выбор/добавление адреса доставки из шапки (для авторизованного). */
export function AddressModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const addresses = useAddressStore((s) => s.addresses)
  const setDefault = useAddressStore((s) => s.setDefault)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (open) setAdding(addresses.length === 0)
  }, [open, addresses.length])

  return (
    <Modal open={open} onClose={onClose} title={t('address.chooseTitle')}>
      {adding ? (
        <div className="flex flex-col gap-3">
          <AddressForm onDone={() => (addresses.length > 0 ? setAdding(false) : onClose())} />
          {addresses.length > 0 ? (
            <button type="button" onClick={() => setAdding(false)} className="text-sm text-ink-muted underline hover:text-ink">
              {t('address.back')}
            </button>
          ) : null}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <ul className="flex flex-col gap-2">
            {addresses.map((address) => (
              <li key={address.id}>
                <button
                  type="button"
                  onClick={() => {
                    setDefault(address.id)
                    onClose()
                  }}
                  className={cn(
                    'flex w-full items-start justify-between gap-3 rounded-control border px-4 py-3 text-left transition-colors duration-[--duration-fast]',
                    address.is_default ? 'border-accent' : 'border-line hover:border-ink-muted',
                  )}
                >
                  <span className="min-w-0 text-base text-ink">{addressLabel(address)}</span>
                  {address.is_default ? <Badge tone="ok">{t('address.default')}</Badge> : null}
                </button>
              </li>
            ))}
          </ul>

          <Button variant="secondary" block onClick={() => setAdding(true)}>
            <IconPlus width={18} height={18} />
            {t('address.add')}
          </Button>
        </div>
      )}
    </Modal>
  )
}
