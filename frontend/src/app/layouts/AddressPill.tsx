import { useState } from 'react'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { IconAddress, IconChevronDown } from '@/shared/ui/Icon'
import { useAuthStore } from '@/features/auth/store'
import { useAddressStore } from '@/features/address/store'
import { AddressModal, addressLabel } from '@/features/address/AddressModal'
import { useUiStore } from '@/app/ui-store'

/**
 * §4а: пилюля адреса доставки. Для авторизованного — открывает выбор/добавление
 * адреса или пункта выдачи; для гостя — модалку входа (§7: адреса привязаны к аккаунту).
 */
export function AddressPill({ className }: { className?: string }) {
  const user = useAuthStore((state) => state.user)
  const openAuth = useUiStore((state) => state.openAuth)
  const addresses = useAddressStore((state) => state.addresses)
  const [open, setOpen] = useState(false)

  const current = addresses.find((a) => a.is_default) ?? addresses[0] ?? null
  const label = current ? addressLabel(current) : t('address.pillEmpty')

  return (
    <>
      <button
        type="button"
        aria-haspopup="dialog"
        aria-label={t('address.chooseTitle')}
        onClick={() => (user ? setOpen(true) : openAuth())}
        className={cn(
          'glass-chrome flex h-14 shrink-0 items-center gap-2 rounded-pill border border-line px-4',
          'text-base text-ink shadow-float transition-colors duration-[--duration-fast] hover:border-ink-muted',
          className,
        )}
      >
        <IconAddress width={18} height={18} className="text-icon" />
        <span className="max-w-[12ch] truncate font-medium">{label}</span>
        <IconChevronDown width={16} height={16} className="text-ink-muted" />
      </button>

      {user ? <AddressModal open={open} onClose={() => setOpen(false)} /> : null}
    </>
  )
}
