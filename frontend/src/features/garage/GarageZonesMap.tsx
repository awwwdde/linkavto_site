import { useState } from 'react'
import { Link } from 'react-router'
import type { GarageVehicle, VehicleType } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'

/**
 * §4а: плоская SVG-схема зон деталей. Контурный силуэт типа техники и
 * 4–6 кликабельных зон. Hover/тап — заливка --color-accent 10%.
 * Клик — переход в /category/{slug}?garage_vehicle_id={id}.
 * Один статичный SVG на тип, без canvas и WebGL (§4, §12).
 */

interface Zone {
  id: string
  label: string
  /** Слаг подкатегории каталога. */
  categorySlug: string
  /** Прямоугольная зона в координатах viewBox 0 0 480 240. */
  x: number
  y: number
  w: number
  h: number
}

/** Зоны легковой техники (базовый силуэт). */
const CAR_ZONES: Zone[] = [
  { id: 'engine', label: 'Двигатель', categorySlug: 'dvigatel', x: 44, y: 96, w: 96, h: 52 },
  { id: 'filters', label: 'Фильтры', categorySlug: 'filtry', x: 148, y: 96, w: 88, h: 52 },
  { id: 'body', label: 'Кузов', categorySlug: 'kuzov', x: 244, y: 96, w: 100, h: 52 },
  { id: 'electrics', label: 'Электрика', categorySlug: 'elektrika', x: 352, y: 96, w: 84, h: 52 },
  { id: 'brakes', label: 'Тормоза', categorySlug: 'tormoznaya-sistema', x: 96, y: 156, w: 120, h: 40 },
  { id: 'suspension', label: 'Подвеска', categorySlug: 'podveska', x: 264, y: 156, w: 120, h: 40 },
]

const ZONES_BY_TYPE: Partial<Record<VehicleType, Zone[]>> = {
  car: CAR_ZONES,
}

/** Контурный силуэт (§4а): монохром, обводка --color-ink. */
function CarSilhouette() {
  return (
    <g fill="none" stroke="var(--color-ink)" strokeWidth={2} strokeLinejoin="round" opacity={0.9}>
      {/* Кузов */}
      <path d="M28 176 L28 150 Q28 142 38 140 L96 132 Q120 100 156 98 L300 98 Q342 102 366 134 L446 146 Q456 148 456 158 L456 176" />
      <line x1="28" y1="176" x2="456" y2="176" />
      {/* Линия окон */}
      <path d="M120 128 Q140 106 168 104 L292 104 Q322 106 340 130" />
      <line x1="228" y1="104" x2="228" y2="130" />
      {/* Колёсные арки */}
      <path d="M96 176 Q100 140 140 140 Q180 140 184 176" />
      <path d="M300 176 Q304 140 344 140 Q384 140 388 176" />
      {/* Колёса */}
      <circle cx="140" cy="184" r="22" />
      <circle cx="140" cy="184" r="9" />
      <circle cx="344" cy="184" r="22" />
      <circle cx="344" cy="184" r="9" />
    </g>
  )
}

export function GarageZonesMap({
  vehicle,
  className,
}: {
  vehicle: GarageVehicle | null
  className?: string
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const zones = (vehicle?.vehicle_type && ZONES_BY_TYPE[vehicle.vehicle_type]) || CAR_ZONES

  const hrefFor = (slug: string) =>
    vehicle ? `/category/legkovye/${slug}?garage_vehicle_id=${vehicle.id}` : `/category/legkovye/${slug}`

  return (
    <div className={cn('mx-auto w-full max-w-[720px]', className)}>
      <svg
        viewBox="0 0 480 240"
        role="group"
        aria-label={t('garage.zonesMap')}
        className="h-auto w-full"
      >
        <CarSilhouette />

        {zones.map((zone) => {
          const active = hovered === zone.id
          return (
            <Link
              key={zone.id}
              to={hrefFor(zone.categorySlug)}
              onMouseEnter={() => setHovered(zone.id)}
              onMouseLeave={() => setHovered(null)}
              onFocus={() => setHovered(zone.id)}
              onBlur={() => setHovered(null)}
              aria-label={zone.label}
            >
              <g className="cursor-pointer">
                <rect
                  x={zone.x}
                  y={zone.y}
                  width={zone.w}
                  height={zone.h}
                  rx={10}
                  className="transition-colors duration-[--duration-fast]"
                  fill={active ? 'color-mix(in srgb, var(--color-accent) 10%, transparent)' : 'transparent'}
                  stroke={active ? 'var(--color-accent)' : 'var(--color-line)'}
                  strokeWidth={active ? 1.5 : 1}
                />
                <text
                  x={zone.x + zone.w / 2}
                  y={zone.y + zone.h / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={13}
                  fontWeight={500}
                  fill={active ? 'var(--color-accent)' : 'var(--color-ink)'}
                  className="select-none"
                >
                  {zone.label}
                </text>
              </g>
            </Link>
          )
        })}
      </svg>
    </div>
  )
}
