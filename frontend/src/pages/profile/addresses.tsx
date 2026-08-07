import { useState } from 'react'
import type { Address } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { Badge, Button, EmptyState } from '@/shared/ui'
import { IconPlus } from '@/shared/ui/Icon'
import { useAddressStore } from '@/features/address/store'
import { AddressMenu } from '@/features/address/AddressMenu'
import { AddressPicker } from '@/features/address/AddressPicker'
import { PROVIDER_LABEL } from '@/features/address/pickup'

type Editing = Address | 'new' | null

export function Component() {
  const addresses = useAddressStore((s) => s.addresses)
  const [editing, setEditing] = useState<Editing>(null)

  const open = editing !== null
  const initial = editing && editing !== 'new' ? editing : undefined

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-md font-semibold">{t('profile.addresses')}</h2>
        <Button variant="primary" onClick={() => setEditing('new')}>
          <IconPlus width={18} height={18} />
          {t('address.add')}
        </Button>
      </div>

      {addresses.length === 0 ? (
        <EmptyState
          title={t('profile.addressesEmptyTitle')}
          text={t('profile.addressesEmptyText')}
          action={
            <Button variant="primary" onClick={() => setEditing('new')}>
              {t('address.add')}
            </Button>
          }
        />
      ) : (
        <ul className="flex flex-col gap-3">
          {addresses.map((address) => (
            <li
              key={address.id}
              className="flex items-start justify-between gap-3 rounded-card bg-surface p-4 shadow-float"
            >
              <div className="flex min-w-0 flex-col gap-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  {address.title ? <span className="font-medium">{address.title}</span> : null}
                  <Badge>{address.delivery_type === 'pickup' ? t('address.pickup') : t('address.courier')}</Badge>
                  {address.is_default ? <Badge tone="ok">{t('address.default')}</Badge> : null}
                </div>

                <span className="text-base text-ink-muted">
                  {address.delivery_type === 'pickup'
                    ? [address.pickup_provider ? PROVIDER_LABEL[address.pickup_provider] : null, address.pickup_point_name]
                        .filter(Boolean)
                        .join(' · ')
                    : address.full_address}
                </span>

                {address.comment ? <span className="text-sm text-ink-muted">{address.comment}</span> : null}

                <div className="flex flex-wrap gap-4 pt-1 text-sm">
                  <button
                    type="button"
                    onClick={() => setEditing(address)}
                    className="text-ink-muted underline hover:text-ink"
                  >
                    {t('address.edit')}
                  </button>
                </div>
              </div>

              {/* Удалить / сделать основным — под троеточием. */}
              <AddressMenu address={address} />
            </li>
          ))}
        </ul>
      )}

      {open ? (
        <AddressPicker key={initial?.id ?? 'new'} open initial={initial} onClose={() => setEditing(null)} />
      ) : null}
    </div>
  )
}
