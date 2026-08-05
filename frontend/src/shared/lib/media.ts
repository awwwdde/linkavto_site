import { useSyncExternalStore } from 'react'

const DESKTOP_QUERY = '(min-width: 1024px)'
const REDUCED_MOTION_QUERY = '(prefers-reduced-motion: reduce)'

function subscribe(query: string, onChange: () => void): () => void {
  const mql = window.matchMedia(query)
  mql.addEventListener('change', onChange)
  return () => mql.removeEventListener('change', onChange)
}

function getSnapshot(query: string): boolean {
  return window.matchMedia(query).matches
}

function getServerSnapshot(): boolean {
  return false
}

export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onStoreChange) => subscribe(query, onStoreChange),
    () => getSnapshot(query),
    getServerSnapshot,
  )
}

/** Desktop / `lg` breakpoint (§11: Lenis только ≥1024px). */
export function useIsDesktop(): boolean {
  return useMediaQuery(DESKTOP_QUERY)
}

export function usePrefersReducedMotion(): boolean {
  return useMediaQuery(REDUCED_MOTION_QUERY)
}

export function hasWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
  } catch {
    return false
  }
}

/** Эвристика слабого устройства — отключаем 3D-сцену гаража. */
export function isLowEndDevice(): boolean {
  const nav = navigator as Navigator & {
    deviceMemory?: number
    connection?: { saveData?: boolean }
  }
  if (typeof nav.deviceMemory === 'number' && nav.deviceMemory <= 4) return true
  if (typeof nav.hardwareConcurrency === 'number' && nav.hardwareConcurrency <= 4) return true
  if (nav.connection?.saveData) return true
  return false
}
