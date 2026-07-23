import { Component as ReactComponent, Suspense, lazy, useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import type { GarageVehicle } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { hasWebGL, isLowEndDevice, useIsDesktop } from '@/shared/lib/media'
import { GarageSceneSvg } from './GarageSceneSvg'
import { GARAGE_ZONES, type ModelGroup } from './zones'

// §12: three/r3f попадают только в этот чанк и грузятся лишь в Гараже.
const Garage3DScene = lazy(() => import('./Garage3DScene'))

/** WebGL-ошибка или сбой загрузки чанка — молча падаем в SVG (§4а). */
class SceneErrorBoundary extends ReactComponent<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}

function zoneGroup(zoneId: string | null): ModelGroup | null {
  return GARAGE_ZONES.find((zone) => zone.id === zoneId)?.group ?? null
}

function ZoneChips({ vehicle, className }: { vehicle: GarageVehicle | null; className?: string }) {
  return (
    <div className={cn('no-scrollbar -mx-4 mt-4 flex gap-2 overflow-x-auto px-4', className)}>
      <span className="sr-only">{t('garage.zones')}</span>
      {GARAGE_ZONES.map((zone) => (
        <Link
          key={zone.id}
          to={
            vehicle
              ? `/category/legkovye/${zone.categorySlug}?garage_vehicle_id=${vehicle.id}`
              : `/category/legkovye/${zone.categorySlug}`
          }
          className="inline-flex min-h-10 shrink-0 items-center rounded-pill bg-surface px-4 text-base shadow-float"
        >
          {zone.label}
        </Link>
      ))}
    </div>
  )
}

function SvgScene({
  vehicle,
  hovered,
  onHover,
}: {
  vehicle: GarageVehicle | null
  hovered: string | null
  onHover: (zone: string | null) => void
}) {
  return (
    <>
      <GarageSceneSvg highlightZone={hovered} />

      <div className="pointer-events-none absolute inset-0 hidden lg:block">
        {GARAGE_ZONES.map((zone) => (
          <Link
            key={zone.id}
            to={
              vehicle
                ? `/category/legkovye/${zone.categorySlug}?garage_vehicle_id=${vehicle.id}`
                : `/category/legkovye/${zone.categorySlug}`
            }
            onMouseEnter={() => onHover(zone.id)}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover(zone.id)}
            onBlur={() => onHover(null)}
            style={{ left: `${zone.x}%`, top: `${zone.y}%` }}
            className="pointer-events-auto absolute inline-flex min-h-10 -translate-x-1/2 -translate-y-1/2 items-center rounded-pill bg-surface px-3 text-sm font-medium shadow-float transition-[box-shadow] duration-[--duration-fast] hover:shadow-lift"
          >
            {zone.label}
          </Link>
        ))}
      </div>
    </>
  )
}

/**
 * §4а: сцена гаража. 3D — только desktop с WebGL и не слабым железом;
 * во всех остальных случаях полноценный SVG-фолбэк с теми же зонами.
 */
export function GarageScene({ vehicle, className }: { vehicle: GarageVehicle | null; className?: string }) {
  const [hovered, setHovered] = useState<string | null>(null)
  const [use3d, setUse3d] = useState(false)
  const isDesktop = useIsDesktop()

  useEffect(() => {
    setUse3d(isDesktop && hasWebGL() && !isLowEndDevice())
  }, [isDesktop])

  const fallback = <SvgScene vehicle={vehicle} hovered={hovered} onHover={setHovered} />

  return (
    <div className={cn('relative mx-auto w-full max-w-[720px]', className)}>
      {use3d ? (
        <SceneErrorBoundary fallback={fallback}>
          <Suspense fallback={fallback}>
            <Garage3DScene vehicle={vehicle} onHoverZone={setHovered} highlighted={zoneGroup(hovered)} />
          </Suspense>
        </SceneErrorBoundary>
      ) : (
        fallback
      )}

      <ZoneChips vehicle={vehicle} className="lg:hidden" />
    </div>
  )
}
