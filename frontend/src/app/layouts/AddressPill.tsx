import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { IconAddress, IconChevronDown } from '@/shared/ui/Icon'

/**
 * §4а: пилюля адреса — отдельно слева от основной пилюли, поэтому не участвует
 * в развороте поиска. Открывает выбор региона.
 * TODO(feature): выбор региона — отдельная фича, пока показываем город по умолчанию.
 */
export function AddressPill({ className }: { className?: string }) {
  return (
    <button
      type="button"
      aria-haspopup="dialog"
      aria-label={t('nav.regionSelect')}
      className={cn(
        'glass-chrome flex h-14 shrink-0 items-center gap-2 rounded-pill border border-line px-4',
        'text-base text-ink shadow-float transition-colors duration-[--duration-fast] hover:border-ink-muted',
        className,
      )}
    >
      <IconAddress width={18} height={18} className="text-icon" />
      <span className="max-w-[9ch] truncate font-medium">{t('nav.regionDefault')}</span>
      <IconChevronDown width={16} height={16} className="text-ink-muted" />
    </button>
  )
}
