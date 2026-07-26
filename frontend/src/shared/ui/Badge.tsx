import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'

// §3.1: скидка — зачёркнутой ценой, не красным бейджем. Красный только для ошибок.
export type BadgeTone = 'neutral' | 'ok' | 'accent'

const TONES: Record<BadgeTone, string> = {
  neutral: 'bg-paper text-ink-muted',
  ok: 'bg-ok-bg text-ok',
  accent: 'bg-ink text-white',
}

export function Badge({
  tone = 'neutral',
  children,
  className,
}: {
  tone?: BadgeTone
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-pill px-2 py-1 text-xs font-medium whitespace-nowrap',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

interface ChipBaseProps {
  active?: boolean
  children: ReactNode
  className?: string
}

const CHIP_BASE =
  'inline-flex min-h-10 items-center gap-2 rounded-pill border px-4 text-base whitespace-nowrap ' +
  'transition-[background-color,border-color,color] duration-[--duration-fast]'

const CHIP_STATE = {
  on: 'border-ink bg-ink text-white',
  off: 'border-line bg-surface text-ink hover:border-ink-muted',
}

export function Chip({
  active = false,
  children,
  className,
  onClick,
  ...rest
}: ChipBaseProps & { onClick?: () => void; 'aria-label'?: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={onClick ? active : undefined}
      className={cn(CHIP_BASE, active ? CHIP_STATE.on : CHIP_STATE.off, className)}
      {...rest}
    >
      {children}
    </button>
  )
}

export function ChipLink({ active = false, children, className, to }: ChipBaseProps & { to: string }) {
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={cn(CHIP_BASE, active ? CHIP_STATE.on : CHIP_STATE.off, className)}
    >
      {children}
    </Link>
  )
}
