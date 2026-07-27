import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconGarage, IconPlus } from '@/shared/ui/Icon'
import { useActiveVehicle } from './store'

/** §6: чип гаража у поиска. Пустое состояние — «Добавить авто». */
export function GarageChip({ className }: { className?: string }) {
  const vehicle = useActiveVehicle()

  const base =
    'inline-flex h-8 max-w-[220px] items-center gap-2 rounded-pill px-3 text-sm whitespace-nowrap ' +
    'transition-colors duration-[--duration-fast]'

  if (!vehicle) {
    return (
      <Link to="/garage" className={cn(base, 'bg-paper text-ink-muted hover:text-ink', className)}>
        <IconPlus width={16} height={16} />
        {t('garage.add')}
      </Link>
    )
  }

  return (
    <Link
      to="/garage"
      className={cn(base, 'bg-paper text-ink font-medium hover:opacity-80', className)}
      title={vehicle.title}
    >
      <IconGarage width={16} height={16} />
      <span className="truncate">{vehicle.title}</span>
    </Link>
  )
}
