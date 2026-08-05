import { useState } from 'react'
import type { Address } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { Badge, Button, EmptyState, Modal, toast } from '@/shared/ui'
import { IconPlus, IconTrash } from '@/shared/ui/Icon'
import { useAddressStore } from '@/features/address/store'
import { AddressForm } from '@/features/address/AddressForm'
import { PROVIDER_LABEL } from '@/features/address/pickup'

type Editing = Address | 'new' | null

export function Component() {
  const addresses = useAddressStore((s) => s.addresses)
  const remove = useAddressStore((s) => s.remove)
  const setDefault = useAddressStore((s) => s.setDefault)
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
                  {!address.is_default ? (
                    <button
                      type="button"
                      onClick={() => setDefault(address.id)}
                      className="text-ink-muted underline hover:text-ink"
                    >
                      {t('address.makeDefault')}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => setEditing(address)}
                    className="text-ink-muted underline hover:text-ink"
                  >
                    {t('address.edit')}
                  </button>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  remove(address.id)
                  toast.ok(t('address.deleted'))
                }}
                aria-label={t('address.deleted')}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control text-ink-muted hover:text-danger"
              >
                <IconTrash />
              </button>
            </li>
          ))}
        </ul>
      )}

      <Modal open={open} onClose={() => setEditing(null)} title={initial ? t('address.edit') : t('address.add')}>
        {open ? (
          <AddressForm key={initial?.id ?? 'new'} initial={initial} onDone={() => setEditing(null)} />
        ) : null}
      </Modal>
    </div>
  )
}
