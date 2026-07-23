import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconMinus, IconPlus, IconTrash } from './Icon'

export interface StepperProps {
  value: number
  onChange: (next: number) => void
  /** §10.2: минимум 1. Ниже — только удаление отдельной кнопкой. */
  min?: number
  max?: number
  onRemove?: () => void
  className?: string
}

export function Stepper({ value, onChange, min = 1, max = 99, onRemove, className }: StepperProps) {
  const canDecrease = value > min
  const showRemove = !canDecrease && Boolean(onRemove)

  return (
    <div
      className={cn('inline-flex h-10 items-center rounded-control border border-line bg-surface', className)}
      role="group"
      aria-label={t('cart.quantity')}
    >
      <button
        type="button"
        onClick={showRemove ? onRemove : () => onChange(Math.max(min, value - 1))}
        aria-label={showRemove ? t('cart.remove') : `${t('cart.quantity')} −1`}
        className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted transition-colors duration-[--duration-fast] hover:text-ink"
      >
        {showRemove ? <IconTrash width={18} height={18} /> : <IconMinus width={18} height={18} />}
      </button>
      <output className="min-w-8 text-center text-base font-medium tabular-nums">{value}</output>
      <button
        type="button"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        aria-label={`${t('cart.quantity')} +1`}
        className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted transition-colors duration-[--duration-fast] hover:text-ink disabled:opacity-40"
      >
        <IconPlus width={18} height={18} />
      </button>
    </div>
  )
}
