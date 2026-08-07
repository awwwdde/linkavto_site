import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import type { Address } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { Badge, Button, EmptyState, Modal } from '@/shared/ui'
import { IconPlus } from '@/shared/ui/Icon'
import { usePrefersReducedMotion } from '@/shared/lib/media'
import { useAddressStore } from './store'
import { AddressMenu } from './AddressMenu'
import { AddressPickerBody } from './AddressPicker'
import { PROVIDER_LABEL } from './pickup'

export function addressLabel(a: Address): string {
  if (a.delivery_type === 'pickup') {
    return [a.pickup_provider ? PROVIDER_LABEL[a.pickup_provider] : null, a.pickup_point_name].filter(Boolean).join(' · ')
  }
  return a.title ? `${a.title}: ${a.full_address}` : a.full_address
}

/**
 * Быстрый выбор адреса из шапки: сначала всегда список сохранённых адресов.
 * «Добавить адрес» разворачивает то же окно до карты — не открывает второе,
 * поэтому переход читается как расширение, а не как подмена.
 */
export function AddressModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const addresses = useAddressStore((s) => s.addresses)
  const setDefault = useAddressStore((s) => s.setDefault)
  const reduced = usePrefersReducedMotion()
  const [adding, setAdding] = useState(false)

  // Каждое открытие начинается со списка — карта только по явному действию.
  useEffect(() => {
    if (open) setAdding(false)
  }, [open])

  const closePicker = () => (addresses.length > 0 ? setAdding(false) : onClose())
  const fade = { duration: reduced ? 0 : 0.18 }

  return (
    <Modal
      open={open}
      onClose={onClose}
      maxWidth={adding ? 1120 : 480}
      title={adding ? t('address.pickerTitle') : t('address.chooseTitle')}
    >
      {/* popLayout: новое содержимое монтируется сразу, старое доигрывает уход —
          окно не ждёт анимации, чтобы показать карту. */}
      <AnimatePresence mode="popLayout" initial={false}>
        {adding ? (
          <motion.div key="picker" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={fade}>
            <AddressPickerBody onCancel={closePicker} onDone={closePicker} />
          </motion.div>
        ) : (
          <motion.div key="list" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={fade}>
            {addresses.length === 0 ? (
              <EmptyState
                title={t('profile.addressesEmptyTitle')}
                text={t('address.emptyText')}
                action={
                  <Button variant="primary" onClick={() => setAdding(true)}>
                    <IconPlus width={18} height={18} />
                    {t('address.add')}
                  </Button>
                }
              />
            ) : (
              <div className="flex flex-col gap-3">
                <ul className="flex flex-col gap-2">
                  {addresses.map((address) => (
                    <li
                      key={address.id}
                      className={cn(
                        'flex items-center gap-1 rounded-control border pr-1 transition-colors duration-[--duration-fast]',
                        address.is_default ? 'border-accent' : 'border-line hover:border-ink-muted',
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setDefault(address.id)
                          onClose()
                        }}
                        className="flex min-w-0 flex-1 items-center justify-between gap-3 px-4 py-3 text-left"
                      >
                        <span className="min-w-0 truncate text-base text-ink">{addressLabel(address)}</span>
                        {address.is_default ? <Badge tone="ok">{t('address.default')}</Badge> : null}
                      </button>

                      <AddressMenu address={address} />
                    </li>
                  ))}
                </ul>

                <Button variant="secondary" block onClick={() => setAdding(true)}>
                  <IconPlus width={18} height={18} />
                  {t('address.add')}
                </Button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Modal>
  )
}
