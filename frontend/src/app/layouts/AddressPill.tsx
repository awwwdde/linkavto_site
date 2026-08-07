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
export function AddressPill({ className, compact }: { className?: string; compact?: boolean }) {
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
        aria-label={compact ? `${t('address.chooseTitle')}: ${label}` : t('address.chooseTitle')}
        title={compact ? label : undefined}
        onClick={() => (user ? setOpen(true) : openAuth())}
        className={
          compact
            ? cn(
                'relative flex h-10 w-10 shrink-0 items-center justify-center rounded-control text-ink',
                'transition-colors duration-[--duration-fast] hover:bg-ink/5',
                className,
              )
            : cn(
                'glass-chrome flex h-14 shrink-0 items-center gap-2 rounded-pill border border-line px-4',
                'text-base text-ink shadow-float transition-colors duration-[--duration-fast] hover:border-ink-muted',
                className,
              )
        }
      >
        {compact ? (
          <>
            <IconAddress />
            {/* Точка-напоминание: адрес ещё не выбран (§4а). */}
            {current ? null : (
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-accent" aria-hidden />
            )}
          </>
        ) : (
          <>
            <IconAddress width={18} height={18} className="text-icon" />
            <span className="max-w-[12ch] truncate font-medium">{label}</span>
            <IconChevronDown width={16} height={16} className="text-ink-muted" />
          </>
        )}
      </button>

      {user ? <AddressModal open={open} onClose={() => setOpen(false)} /> : null}
    </>
  )
}
