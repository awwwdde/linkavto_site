import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/cn'

const CONTROL =
  'h-10 w-full rounded-control border border-line bg-surface px-3 text-base text-ink placeholder:text-ink-muted ' +
  'transition-[border-color] duration-[--duration-fast] focus:border-ink-muted focus:outline-none ' +
  'aria-[invalid=true]:border-danger'

interface FieldShellProps {
  id: string
  label?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
}

function FieldShell({ id, label, hint, error, children, className }: FieldShellProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {label ? (
        <label htmlFor={id} className="text-sm font-medium text-ink-muted">
          {label}
        </label>
      ) : null}
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-sm text-ink-muted">
          {hint}
        </p>
      ) : null}
    </div>
  )
}

export type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> & {
  label?: string
  hint?: string
  error?: string
  wrapperClassName?: string
}

export function Input({ label, hint, error, className, wrapperClassName, ...rest }: InputProps) {
  const id = useId()
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} className={wrapperClassName}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(CONTROL, className)}
        {...rest}
      />
    </FieldShell>
  )
}

export type SelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> & {
  label?: string
  hint?: string
  error?: string
  wrapperClassName?: string
}

export function Select({ label, hint, error, className, wrapperClassName, children, ...rest }: SelectProps) {
  const id = useId()
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} className={wrapperClassName}>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(CONTROL, 'appearance-none pr-8', className)}
        {...rest}
      >
        {children}
      </select>
    </FieldShell>
  )
}

export type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> & { label: ReactNode }

export function Checkbox({ label, className, ...rest }: CheckboxProps) {
  const id = useId()
  return (
    <div className="flex min-h-10 items-center gap-3">
      <input
        id={id}
        type="checkbox"
        className={cn('h-5 w-5 shrink-0 accent-[--color-accent]', className)}
        {...rest}
      />
      <label htmlFor={id} className="cursor-pointer text-base text-ink">
        {label}
      </label>
    </div>
  )
}

export type RadioProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> & {
  label: ReactNode
  description?: ReactNode
}

export function Radio({ label, description, className, ...rest }: RadioProps) {
  const id = useId()
  return (
    <div className="flex min-h-10 items-start gap-3">
      <input
        id={id}
        type="radio"
        className={cn('mt-1 h-5 w-5 shrink-0 accent-[--color-accent]', className)}
        {...rest}
      />
      <label htmlFor={id} className="cursor-pointer text-base text-ink">
        {label}
        {description ? <span className="block text-sm text-ink-muted">{description}</span> : null}
      </label>
    </div>
  )
}
