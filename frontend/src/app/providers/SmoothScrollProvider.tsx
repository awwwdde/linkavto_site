import { useEffect } from 'react'
import { useIsDesktop, usePrefersReducedMotion } from '@/shared/lib/media'

/**
 * §11: Lenis только на ≥1024px и только без prefers-reduced-motion.
 * Импорт динамический — на mobile чанк вообще не грузится (§12).
 */
export function SmoothScrollProvider() {
  const isDesktop = useIsDesktop()
  const reducedMotion = usePrefersReducedMotion()

  useEffect(() => {
    if (!isDesktop || reducedMotion) return

    let disposed = false
    let cleanup: (() => void) | undefined

    void (async () => {
      const [{ default: Lenis }, { gsap }, { ScrollTrigger }] = await Promise.all([
        import('lenis'),
        import('gsap'),
        import('gsap/ScrollTrigger'),
      ])
      if (disposed) return

      gsap.registerPlugin(ScrollTrigger)
      const lenis = new Lenis({ autoRaf: false })

      const onScroll = () => ScrollTrigger.update()
      lenis.on('scroll', onScroll)

      const tick = (time: number) => lenis.raf(time * 1000)
      gsap.ticker.add(tick)
      gsap.ticker.lagSmoothing(0)

      cleanup = () => {
        gsap.ticker.remove(tick)
        lenis.off('scroll', onScroll)
        lenis.destroy()
      }
    })()

    return () => {
      disposed = true
      cleanup?.()
    }
  }, [isDesktop, reducedMotion])

  return null
}
