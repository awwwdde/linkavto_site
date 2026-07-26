import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'md' | 'lg' | 'icon'

const VARIANTS: Record<ButtonVariant, string> = {
  // primary = --color-accent, единственный цвет действия (§3.1)
  primary: 'bg-accent text-white hover:bg-accent-hover',
  secondary: 'bg-surface text-ink border border-line hover:border-ink-muted',
  ghost: 'text-ink hover:bg-ink/5',
  danger: 'bg-danger-bg text-danger hover:bg-danger/15',
}

const SIZES: Record<ButtonSize, string> = {
  md: 'h-10 px-4 text-base',
  lg: 'h-12 px-6 text-md',
  icon: 'h-10 w-10',
}

const BASE =
  'inline-flex items-center justify-center gap-2 rounded-control font-medium select-none ' +
  'transition-[background-color,border-color,color,transform,opacity] duration-[--duration-fast] ' +
  'active:scale-[0.96] disabled:pointer-events-none disabled:opacity-50'

interface CommonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  block?: boolean
  children?: ReactNode
  className?: string
}

export type ButtonProps = CommonProps & ButtonHTMLAttributes<HTMLButtonElement>

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  block = false,
  className,
  children,
  disabled,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled ?? loading}
      aria-busy={loading || undefined}
      className={cn(BASE, VARIANTS[variant], SIZES[size], block && 'w-full', className)}
      {...rest}
    >
      {loading ? <Spinner /> : children}
    </button>
  )
}

export type ButtonLinkProps = CommonProps & {
  to: string
  'aria-label'?: string
  onClick?: () => void
}

export function ButtonLink({ variant = 'secondary', size = 'md', block, className, children, to, ...rest }: ButtonLinkProps) {
  return (
    <Link to={to} className={cn(BASE, VARIANTS[variant], SIZES[size], block && 'w-full', className)} {...rest}>
      {children}
    </Link>
  )
}

function Spinner() {
  return (
    <span
      className="h-4 w-4 animate-spin rounded-pill border-2 border-current border-t-transparent"
      aria-hidden="true"
    />
  )
}
