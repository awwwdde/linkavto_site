import { useState } from 'react'
import { Link } from 'react-router'
import type { GarageVehicle, VehicleType } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { vehicleMeta } from '@/shared/lib/vehicle-types'

/**
 * §4а: интерактивная карта зон авто. На подложке — изображение машины
 * (реальный рендер из `public/garage/`, если есть), иначе контурный SVG-силуэт.
 * Поверх — светящиеся точки-зоны: точка → линия-выноска → подпись. Клик по
 * зоне ведёт в /category/{root}/{slug}?garage_vehicle_id={id}.
 *
 * Всё в системе координат viewBox 0 0 480 280 — и подложка, и точки, поэтому
 * координаты точек легко подогнать под конкретную картинку.
 */

interface Zone {
  id: string
  label: string
  /** Слаг подкатегории каталога. */
  categorySlug: string
  /** Точка на детали (viewBox). */
  dx: number
  dy: number
  /** Центр подписи (viewBox). */
  lx: number
  ly: number
}

/**
 * Реальные рендеры по типам техники. Положи файл в `public/garage/` и укажи путь —
 * подхватится автоматически (координаты точек подгоним под картинку). Пока пусто →
 * рисуем контурный силуэт.
 */
const CAR_IMAGE: Partial<Record<VehicleType, string>> = {
  // car: '/garage/car-side.webp',
}

const CAR_ZONES: Zone[] = [
  { id: 'engine', label: 'Двигатель', categorySlug: 'dvigatel', dx: 96, dy: 126, lx: 66, ly: 40 },
  { id: 'filters', label: 'Фильтры', categorySlug: 'filtry', dx: 150, dy: 120, lx: 176, ly: 40 },
  { id: 'body', label: 'Кузов', categorySlug: 'kuzov', dx: 252, dy: 116, lx: 268, ly: 40 },
  { id: 'electrics', label: 'Электрика', categorySlug: 'elektrika', dx: 330, dy: 122, lx: 388, ly: 40 },
  { id: 'brakes', label: 'Тормоза', categorySlug: 'tormoznaya-sistema', dx: 140, dy: 184, lx: 104, ly: 252 },
  { id: 'suspension', label: 'Подвеска', categorySlug: 'podveska', dx: 344, dy: 184, lx: 384, ly: 252 },
]

const ZONES_BY_TYPE: Partial<Record<VehicleType, Zone[]>> = {
  car: CAR_ZONES,
}

/** Контурный силуэт-фолбэк (§4а): монохром, тонкая обводка — чтобы точки читались. */
function CarSilhouette() {
  return (
    <g fill="none" stroke="var(--color-ink)" strokeWidth={2} strokeLinejoin="round" opacity={0.28}>
      <path d="M28 176 L28 150 Q28 142 38 140 L96 132 Q120 100 156 98 L300 98 Q342 102 366 134 L446 146 Q456 148 456 158 L456 176" />
      <line x1="28" y1="176" x2="456" y2="176" />
      <path d="M120 128 Q140 106 168 104 L292 104 Q322 106 340 130" />
      <line x1="228" y1="104" x2="228" y2="130" />
      <path d="M96 176 Q100 140 140 140 Q180 140 184 176" />
      <path d="M300 176 Q304 140 344 140 Q384 140 388 176" />
      <circle cx="140" cy="184" r="22" />
      <circle cx="140" cy="184" r="9" />
      <circle cx="344" cy="184" r="22" />
      <circle cx="344" cy="184" r="9" />
    </g>
  )
}

function ZoneHotspot({
  zone,
  href,
  active,
  onEnter,
  onLeave,
}: {
  zone: Zone
  href: string
  active: boolean
  onEnter: () => void
  onLeave: () => void
}) {
  const w = zone.label.length * 7.2 + 22
  const h = 26
  const rectX = zone.lx - w / 2
  const rectY = zone.ly - h / 2
  // Линия-выноска идёт к ближней грани подписи.
  const anchorY = zone.ly < zone.dy ? zone.ly + h / 2 : zone.ly - h / 2

  return (
    <Link
      to={href}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onFocus={onEnter}
      onBlur={onLeave}
      aria-label={zone.label}
    >
      <g className="cursor-pointer">
        {/* Линия-выноска */}
        <line
          x1={zone.dx}
          y1={zone.dy}
          x2={zone.lx}
          y2={anchorY}
          stroke={active ? 'var(--color-accent)' : 'var(--color-line)'}
          strokeWidth={active ? 1.5 : 1}
          className="transition-colors duration-[--duration-fast]"
        />

        {/* Светящаяся точка */}
        {!active ? (
          <circle cx={zone.dx} cy={zone.dy} r={7} fill="var(--color-accent)" opacity={0.35} className="hotspot-pulse" />
        ) : null}
        <circle
          cx={zone.dx}
          cy={zone.dy}
          r={active ? 9 : 7}
          fill="var(--color-accent)"
          opacity={0.18}
          className="transition-all duration-[--duration-fast]"
        />
        <circle
          cx={zone.dx}
          cy={zone.dy}
          r={active ? 5 : 4}
          fill="var(--color-accent)"
          className="transition-all duration-[--duration-fast]"
        />
        <circle cx={zone.dx} cy={zone.dy} r={1.6} fill="var(--color-surface)" />

        {/* Подпись-пилюля */}
        <rect
          x={rectX}
          y={rectY}
          width={w}
          height={h}
          rx={13}
          fill="var(--color-surface)"
          stroke={active ? 'var(--color-accent)' : 'var(--color-line)'}
          strokeWidth={active ? 1.5 : 1}
          className="transition-colors duration-[--duration-fast]"
        />
        <text
          x={zone.lx}
          y={zone.ly}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={12.5}
          fontWeight={500}
          fill={active ? 'var(--color-accent)' : 'var(--color-ink)'}
          className="select-none"
        >
          {zone.label}
        </text>
      </g>
    </Link>
  )
}

export function GarageZonesMap({ vehicle, className }: { vehicle: GarageVehicle | null; className?: string }) {
  const [hovered, setHovered] = useState<string | null>(null)
  const type = vehicle?.vehicle_type ?? 'car'
  const zones = ZONES_BY_TYPE[type] ?? CAR_ZONES
  const image = CAR_IMAGE[type] ?? null
  const root = vehicleMeta(vehicle?.vehicle_type)?.slug ?? 'legkovye'

  const hrefFor = (slug: string) =>
    vehicle ? `/category/${root}/${slug}?garage_vehicle_id=${vehicle.id}` : `/category/${root}/${slug}`

  return (
    <div className={cn('mx-auto w-full max-w-[760px]', className)}>
      <svg viewBox="0 0 480 280" role="group" aria-label={t('garage.zonesMap')} className="h-auto w-full">
        {image ? (
          <image href={image} x={16} y={70} width={448} height={150} preserveAspectRatio="xMidYMid meet" />
        ) : (
          <CarSilhouette />
        )}

        {zones.map((zone) => (
          <ZoneHotspot
            key={zone.id}
            zone={zone}
            href={hrefFor(zone.categorySlug)}
            active={hovered === zone.id}
            onEnter={() => setHovered(zone.id)}
            onLeave={() => setHovered(null)}
          />
        ))}
      </svg>
    </div>
  )
}
