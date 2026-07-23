import { useMemo } from 'react'
import * as THREE from 'three'
import type { ModelGroup } from './zones'

/**
 * §4а: процедурная low-poly модель седана, собранная кодом из примитивов
 * и одной экструзии. 200–500 полигонов, flatShading, без текстур.
 * Палитра — оттенки цвета транспорта, стёкла светлее, низ темнее.
 */
const PALETTE = {
  bodyTop: '#378ADD',
  bodyLit: '#85B7EB',
  glass: '#B5D4F4',
  glassLit: '#EAF3FB',
  under: '#0C447C',
  wheel: '#185FA5',
  wheelLit: '#85B7EB',
} as const

function useBodyGeometry() {
  return useMemo(() => {
    // Силуэт кузова сбоку: капот — стойка — крыша — багажник.
    const shape = new THREE.Shape()
    shape.moveTo(-2.1, 0.3)
    shape.lineTo(-2.0, 0.95)
    shape.lineTo(-1.0, 1.05)
    shape.lineTo(-0.55, 1.62)
    shape.lineTo(0.75, 1.62)
    shape.lineTo(1.25, 1.0)
    shape.lineTo(2.05, 0.86)
    shape.lineTo(2.15, 0.32)
    shape.lineTo(-2.1, 0.3)

    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: 1.9,
      bevelEnabled: true,
      bevelSize: 0.09,
      bevelThickness: 0.09,
      bevelSegments: 1,
      curveSegments: 1,
    })
    geometry.translate(0, 0, -0.95)
    geometry.computeVertexNormals()
    return geometry
  }, [])
}

function Wheel({ position, highlighted }: { position: [number, number, number]; highlighted: boolean }) {
  return (
    <group position={position} rotation={[Math.PI / 2, 0, 0]}>
      <mesh castShadow={false}>
        <cylinderGeometry args={[0.45, 0.45, 0.28, 8]} />
        <meshStandardMaterial color={highlighted ? PALETTE.wheelLit : PALETTE.wheel} flatShading />
      </mesh>
    </group>
  )
}

function BrakeDisc({ position, highlighted }: { position: [number, number, number]; highlighted: boolean }) {
  return (
    <mesh position={position} rotation={[Math.PI / 2, 0, 0]}>
      <cylinderGeometry args={[0.24, 0.24, 0.32, 8]} />
      <meshStandardMaterial color={highlighted ? PALETTE.glassLit : PALETTE.bodyLit} flatShading />
    </mesh>
  )
}

export function SedanModel({ highlighted }: { highlighted: ModelGroup | null }) {
  const bodyGeometry = useBodyGeometry()
  const lit = (group: ModelGroup) => highlighted === group

  return (
    <group position={[0, -0.4, 0]}>
      <mesh geometry={bodyGeometry}>
        <meshStandardMaterial color={lit('body') ? PALETTE.bodyLit : PALETTE.bodyTop} flatShading />
      </mesh>

      {/* Капот — отдельная грань, чтобы подсвечивать зону двигателя/фильтров */}
      <mesh position={[1.5, 0.99, 0]} rotation={[0, 0, -0.08]}>
        <boxGeometry args={[1.1, 0.06, 1.75]} />
        <meshStandardMaterial color={lit('hood') ? PALETTE.glassLit : PALETTE.bodyLit} flatShading />
      </mesh>

      {/* Стёкла */}
      <mesh position={[0.1, 1.35, 0]}>
        <boxGeometry args={[1.25, 0.5, 1.82]} />
        <meshStandardMaterial color={lit('glass') ? PALETTE.glassLit : PALETTE.glass} flatShading />
      </mesh>

      {/* Низ темнее */}
      <mesh position={[0, 0.32, 0]}>
        <boxGeometry args={[4.1, 0.18, 1.86]} />
        <meshStandardMaterial color={PALETTE.under} flatShading />
      </mesh>

      <Wheel position={[1.3, 0.42, 0.98]} highlighted={lit('wheels')} />
      <Wheel position={[1.3, 0.42, -0.98]} highlighted={lit('wheels')} />
      <Wheel position={[-1.35, 0.42, 0.98]} highlighted={lit('wheels')} />
      <Wheel position={[-1.35, 0.42, -0.98]} highlighted={lit('wheels')} />

      <BrakeDisc position={[1.3, 0.42, 0.99]} highlighted={lit('brakes')} />
      <BrakeDisc position={[-1.35, 0.42, 0.99]} highlighted={lit('brakes')} />

      {/* Плоский эллипс-«подиум» вместо настоящей тени (§4а) */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[2.9, 24]} />
        <meshBasicMaterial color="#DCE6F0" />
      </mesh>
    </group>
  )
}
