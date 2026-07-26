import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'

/**
 * §3.2: двухтоновый заголовок — сигнатурный приём, обязателен для h1 и
 * заголовков секций. Первая фраза `--color-ink`, продолжение `--color-ink-ghost`.
 * На тёмной полосе (§3.4) второй тон — `--color-ink-ghost-dark`.
 */
export function SectionHeading({
  lead,
  ghost,
  as = 'h2',
  size = 'lg',
  dark = false,
  className,
}: {
  lead: ReactNode
  ghost?: ReactNode
  as?: 'h1' | 'h2' | 'h3'
  size?: 'lg' | 'xl' | 'hero'
  dark?: boolean
  className?: string
}) {
  const Tag = as
  const sizeClass =
    size === 'hero'
      ? 'text-2xl lg:text-3xl'
      : size === 'xl'
        ? 'text-xl lg:text-2xl'
        : 'text-lg lg:text-xl'

  return (
    <Tag
      className={cn(
        'font-semibold text-balance',
        sizeClass,
        dark ? 'text-paper' : 'text-ink',
        className,
      )}
    >
      {lead}
      {ghost ? <span className={dark ? 'text-ink-ghost-dark' : 'text-ink-ghost'}> {ghost}</span> : null}
    </Tag>
  )
}
