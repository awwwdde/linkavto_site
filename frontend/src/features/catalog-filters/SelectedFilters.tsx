import { useQuery } from '@tanstack/react-query'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { formatPrice } from '@/shared/lib/format'
import { IconClose } from '@/shared/ui/Icon'
import {
  fetchVehicleBrands,
  fetchVehicleClasses,
  fetchVehicleGenerations,
  fetchVehicleModels,
  fetchVehicleModifications,
} from '@/features/vehicle-filter/api'
import { useActiveVehicle } from '@/features/garage/store'
import { useCatalogParams, type VehicleLevel } from './useCatalogParams'

const KIND_LABEL: Record<string, string> = {
  car: 'Легковые',
  truck: 'Грузовые',
  moto: 'Мото',
  special: 'Спецтехника',
}

interface Tag {
  id: string
  label: string
  onRemove: () => void
}

/** Активный фильтр — выделенный тег, который можно снять одним нажатием. */
function FilterTag({ tag }: { tag: Tag }) {
  return (
    <span className="inline-flex min-h-10 shrink-0 items-center gap-1 rounded-pill border border-ink bg-ink pr-1 pl-3 text-sm text-white">
      <span className="max-w-[220px] truncate">{tag.label}</span>
      <button
        type="button"
        onClick={tag.onRemove}
        aria-label={`Снять фильтр: ${tag.label}`}
        className="flex h-8 w-8 items-center justify-center rounded-pill text-white/70 transition-colors duration-[--duration-fast] hover:text-white"
      >
        <IconClose width={14} height={14} />
      </button>
    </span>
  )
}

export function SelectedFilters({ className }: { className?: string }) {
  const { params, applyVehicle, setParam, toggleInList, reset, activeCount } = useCatalogParams()
  const garageVehicle = useActiveVehicle()
  const kind = params.vehicleType

  // Запросы уже прогреты фильтром — берём из кэша, чтобы показать имена, а не слаги.
  const classes = useQuery({
    queryKey: ['vehicle', 'classes', kind],
    queryFn: () => fetchVehicleClasses(kind),
    enabled: Boolean(params.vehicleClass),
  })
  const brands = useQuery({
    queryKey: ['vehicle', 'brands', kind, params.vehicleClass],
    queryFn: () => fetchVehicleBrands(kind, params.vehicleClass),
    enabled: Boolean(params.brand),
  })
  const models = useQuery({
    queryKey: ['vehicle', 'models', kind, params.brand],
    queryFn: () => fetchVehicleModels(kind, params.brand),
    enabled: Boolean(params.model),
  })
  const generations = useQuery({
    queryKey: ['vehicle', 'generations', kind, params.model],
    queryFn: () => fetchVehicleGenerations(kind, params.model),
    enabled: Boolean(params.generation),
  })
  const modifications = useQuery({
    queryKey: ['vehicle', 'modifications', kind, params.generation],
    queryFn: () => fetchVehicleModifications(kind, params.generation),
    enabled: Boolean(params.modification),
  })

  const nameOf = (options: { slug: string; name: string }[] | undefined, slug: string) =>
    options?.find((option) => option.slug === slug)?.name ?? slug

  const tags: Tag[] = []

  const vehicleTag = (level: VehicleLevel, slug: string, label: string) => ({
    id: `${level}:${slug}`,
    label,
    onRemove: () => applyVehicle({ [level]: null }, level),
  })

  if (params.garageVehicleId && garageVehicle) {
    tags.push({
      id: 'garage',
      label: garageVehicle.title,
      onRemove: () => setParam('garage_vehicle_id', null),
    })
  }

  if (kind) tags.push(vehicleTag('vehicleType', kind, KIND_LABEL[kind] ?? kind))
  if (params.vehicleClass)
    tags.push(vehicleTag('vehicleClass', params.vehicleClass, nameOf(classes.data, params.vehicleClass)))
  if (params.brand) tags.push(vehicleTag('brand', params.brand, nameOf(brands.data, params.brand)))
  if (params.model) tags.push(vehicleTag('model', params.model, nameOf(models.data, params.model)))
  if (params.generation)
    tags.push(vehicleTag('generation', params.generation, nameOf(generations.data, params.generation)))
  if (params.modification)
    tags.push(vehicleTag('modification', params.modification, nameOf(modifications.data, params.modification)))

  for (const value of params.manufacturers) {
    tags.push({ id: `manufacturer:${value}`, label: value, onRemove: () => toggleInList('manufacturer', value) })
  }
  for (const value of params.productBrands) {
    tags.push({ id: `product_brand:${value}`, label: value, onRemove: () => toggleInList('product_brand', value) })
  }

  if (params.priceMin || params.priceMax) {
    const from = params.priceMin ? `${t('catalog.priceFrom')} ${formatPrice(params.priceMin)}` : ''
    const to = params.priceMax ? `${t('catalog.priceTo')} ${formatPrice(params.priceMax)}` : ''
    tags.push({
      id: 'price',
      label: `${t('catalog.price')}: ${[from, to].filter(Boolean).join(' ')}`,
      onRemove: () => {
        setParam('price_min', null)
        setParam('price_max', null)
      },
    })
  }

  if (params.inStock) tags.push({ id: 'in_stock', label: t('catalog.inStock'), onRemove: () => setParam('in_stock', null) })
  if (params.onOrder) tags.push({ id: 'on_order', label: t('catalog.onOrder'), onRemove: () => setParam('on_order', null) })
  if (params.isOriginal)
    tags.push({ id: 'is_original', label: t('catalog.isOriginal'), onRemove: () => setParam('is_original', null) })

  for (const [key, value] of Object.entries(params.tireWheel)) {
    if (!value) continue
    tags.push({ id: `${key}:${value}`, label: `${value}`, onRemove: () => setParam(key, null) })
  }

  if (tags.length === 0) return null

  return (
    <div className={cn('no-scrollbar flex items-center gap-2 overflow-x-auto', className)}>
      {tags.map((tag) => (
        <FilterTag key={tag.id} tag={tag} />
      ))}

      {activeCount > 1 ? (
        <button
          type="button"
          onClick={reset}
          className="shrink-0 px-2 text-sm text-ink-muted underline transition-colors duration-[--duration-fast] hover:text-ink"
        >
          {t('catalog.filtersReset')}
        </button>
      ) : null}
    </div>
  )
}
