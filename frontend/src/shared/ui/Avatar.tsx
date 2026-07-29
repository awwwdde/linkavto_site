import { cn } from '@/shared/lib/cn'

export interface AvatarProps {
  src?: string | null
  /** Имя для инициалов-фолбэка и alt. */
  name?: string | null
  size?: number
  /** Скругление: круг (по умолчанию) или карточка — для логотипов магазинов. */
  shape?: 'circle' | 'rounded'
  className?: string
}

function initials(name: string | null | undefined): string {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean).slice(0, 2)
  const value = parts.map((part) => part[0]?.toUpperCase() ?? '').join('')
  return value || '—'
}

/**
 * Аватар пользователя / логотип магазина. Есть фото — показываем его,
 * нет — монохромные инициалы (§3.1, без цветных подложек).
 */
export function Avatar({ src, name, size = 40, shape = 'circle', className }: AvatarProps) {
  const radius = shape === 'circle' ? 'rounded-full' : 'rounded-card'
  const dimension = { width: size, height: size }

  if (src) {
    return (
      <img
        src={src}
        alt={name ?? ''}
        style={dimension}
        className={cn('shrink-0 object-cover', radius, className)}
      />
    )
  }

  return (
    <span
      style={dimension}
      aria-hidden
      className={cn(
        'flex shrink-0 items-center justify-center bg-ink/5 font-semibold text-ink',
        radius,
        className,
      )}
    >
      <span style={{ fontSize: Math.round(size * 0.4) }}>{initials(name)}</span>
    </span>
  )
}
