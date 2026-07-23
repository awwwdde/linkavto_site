import { useRef, useState } from 'react'
import { Link } from 'react-router'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import type { Group } from 'three'
import type { GarageVehicle } from '@/shared/api/types'
import { usePrefersReducedMotion } from '@/shared/lib/media'
import { SedanModel } from './SedanModel'
import { GARAGE_ZONES, type ModelGroup } from './zones'

/** Авто-вращение ~0.15 рад/с, пауза при взаимодействии (§11). */
function RotatingModel({
  paused,
  highlighted,
}: {
  paused: boolean
  highlighted: ModelGroup | null
}) {
  const ref = useRef<Group>(null)
  const reducedMotion = usePrefersReducedMotion()

  useFrame((_state, delta) => {
    if (!ref.current || paused || reducedMotion) return
    ref.current.rotation.y += 0.15 * delta
  })

  return (
    <group ref={ref}>
      <SedanModel highlighted={highlighted} />
    </group>
  )
}

export interface Garage3DSceneProps {
  vehicle: GarageVehicle | null
  onHoverZone: (zone: string | null) => void
  highlighted: ModelGroup | null
}

export default function Garage3DScene({ vehicle, onHoverZone, highlighted }: Garage3DSceneProps) {
  const [interacting, setInteracting] = useState(false)

  const zoneHref = (slug: string) =>
    vehicle ? `/category/legkovye/${slug}?garage_vehicle_id=${vehicle.id}` : `/category/legkovye/${slug}`

  return (
    <div className="relative aspect-[16/10] w-full">
      <Canvas
        camera={{ position: [5.2, 3.2, 5.2], fov: 34 }}
        dpr={[1, 1.75]}
        gl={{ antialias: true, powerPreference: 'high-performance' }}
        onPointerEnter={() => setInteracting(true)}
        onPointerLeave={() => setInteracting(false)}
      >
        {/* Освещение: ambient + один directional, без HDR-окружений (§4а). */}
        <ambientLight intensity={0.85} />
        <directionalLight position={[4, 6, 3]} intensity={1.1} />

        <RotatingModel paused={interacting} highlighted={highlighted} />

        <OrbitControls
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 3.4}
          maxPolarAngle={Math.PI / 3.4}
          onStart={() => setInteracting(true)}
        />
      </Canvas>

      {/* Чипы зон — обычный DOM поверх canvas: доступны с клавиатуры. */}
      <div className="pointer-events-none absolute inset-0">
        {GARAGE_ZONES.map((zone) => (
          <Link
            key={zone.id}
            to={zoneHref(zone.categorySlug)}
            style={{ left: `${zone.x}%`, top: `${zone.y}%` }}
            onMouseEnter={() => onHoverZone(zone.id)}
            onMouseLeave={() => onHoverZone(null)}
            onFocus={() => onHoverZone(zone.id)}
            onBlur={() => onHoverZone(null)}
            className="pointer-events-auto absolute inline-flex min-h-10 -translate-x-1/2 -translate-y-1/2 items-center rounded-pill bg-surface px-3 text-sm font-medium shadow-float transition-[box-shadow] duration-[--duration-fast] hover:shadow-lift"
          >
            {zone.label}
          </Link>
        ))}
      </div>
    </div>
  )
}
