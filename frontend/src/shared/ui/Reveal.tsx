import type { ReactNode } from 'react'
import { motion } from 'motion/react'
import { usePrefersReducedMotion } from '@/shared/lib/media'

export interface RevealProps {
  children: ReactNode
  className?: string
  /** Задержка старта, с — для лёгкого каскада соседних блоков. */
  delay?: number
}

/**
 * §11: блок мягко проявляется при попадании во вьюпорт (один раз).
 * Уважает prefers-reduced-motion — тогда рендерится статично, без обёртки-анимации.
 */
export function Reveal({ children, className, delay = 0 }: RevealProps) {
  const reduced = usePrefersReducedMotion()

  if (reduced) return <div className={className}>{children}</div>

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.div>
  )
}
