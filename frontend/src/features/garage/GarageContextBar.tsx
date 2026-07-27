import { Link } from 'react-router'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { IconChevronRight, IconCompatOk, IconGarage } from '@/shared/ui/Icon'
import { useCatalogParams } from '@/features/catalog-filters/useCatalogParams'
import { useActiveVehicle } from './store'

/**
 * Гараж как сквозной контекст просмотра (§7): полоса над списком каталога.
 * — нет авто → мягкий CTA добавить;
 * — авто есть, фильтр выкл → «Смотрим для {авто}» + включить «только подходящие»;
 * — фильтр вкл → ok-подсветка «Показываем только для {авто}» + вернуть все.
 * Совместимость держится в URL-параметре garage_vehicle_id (как и в VehicleFilter).
 */
export function GarageContextBar({ className }: { className?: string }) {
  const vehicle = useActiveVehicle()
  const { params, setParam } = useCatalogParams()
  const active = Boolean(params.garageVehicleId)

  if (!vehicle) {
    return (
      <Link
        to="/garage"
        className={cn(
          'flex items-center gap-3 rounded-card border border-dashed border-line bg-surface px-4 py-3',
          'text-sm text-ink-muted transition-colors duration-[--duration-base] hover:border-ink-muted hover:text-ink',
          className,
        )}
      >
        <IconGarage width={18} height={18} className="shrink-0" />
        <span className="min-w-0 flex-1">{t('garageContext.addPrompt')}</span>
        <IconChevronRight width={16} height={16} className="shrink-0" />
      </Link>
    )
  }

  const btnBase =
    'inline-flex h-9 shrink-0 items-center rounded-control px-3.5 text-sm font-medium ' +
    'transition-colors duration-[--duration-fast]'

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-2 rounded-card border px-4 py-3',
        'transition-colors duration-[--duration-base]',
        active ? 'border-ok/30 bg-ok-bg' : 'border-line bg-surface',
        className,
      )}
    >
      <span className="inline-flex min-w-0 items-center gap-2">
        <IconCompatOk
          width={18}
          height={18}
          className={cn('shrink-0', active ? 'text-ok' : 'text-icon')}
        />
        <span className="min-w-0 truncate">
          <span className={cn('text-xs', active ? 'text-ok/80' : 'text-ink-muted')}>
            {active ? t('garageContext.showingFor') : t('garageContext.lookingAt')}
          </span>{' '}
          <span className={cn('font-medium', active ? 'text-ok' : 'text-ink')}>{vehicle.title}</span>
        </span>
      </span>

      <div className="ml-auto flex items-center gap-2">
        <Link
          to="/garage"
          className={cn(
            'text-sm underline underline-offset-2',
            active ? 'text-ok hover:opacity-80' : 'text-ink-muted hover:text-ink',
          )}
        >
          {t('garage.switch')}
        </Link>
        {active ? (
          <button
            type="button"
            onClick={() => setParam('garage_vehicle_id', null)}
            className={cn(btnBase, 'border border-ok/30 bg-surface text-ok hover:bg-surface/70')}
          >
            {t('garageContext.showAll')}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setParam('garage_vehicle_id', String(vehicle.id))}
            className={cn(btnBase, 'bg-ink text-white hover:bg-ink/90')}
          >
            {t('garageContext.onlyFits')}
          </button>
        )}
      </div>
    </div>
  )
}
