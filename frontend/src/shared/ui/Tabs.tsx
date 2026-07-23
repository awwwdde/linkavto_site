import { NavLink } from 'react-router'
import { cn } from '@/shared/lib/cn'

export interface TabItem {
  to: string
  label: string
  end?: boolean
}

/** Табы-роуты (профиль, карточка товара на mobile). */
export function TabsNav({ items, className }: { items: TabItem[]; className?: string }) {
  return (
    <nav className={cn('no-scrollbar flex gap-1 overflow-x-auto', className)}>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            cn(
              'flex min-h-10 items-center rounded-control px-4 text-base whitespace-nowrap transition-colors duration-[--duration-fast]',
              isActive ? 'bg-ink text-white' : 'text-ink-muted hover:bg-ink/5',
            )
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}

export interface TabsProps<T extends string> {
  value: T
  onChange: (value: T) => void
  items: { value: T; label: string }[]
  className?: string
  'aria-label': string
}

export function Tabs<T extends string>({ value, onChange, items, className, ...rest }: TabsProps<T>) {
  return (
    <div role="tablist" className={cn('no-scrollbar flex gap-1 overflow-x-auto', className)} {...rest}>
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          role="tab"
          aria-selected={item.value === value}
          onClick={() => onChange(item.value)}
          className={cn(
            'flex min-h-10 items-center rounded-control px-4 text-base whitespace-nowrap transition-colors duration-[--duration-fast]',
            item.value === value ? 'bg-ink text-white' : 'text-ink-muted hover:bg-ink/5',
          )}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
