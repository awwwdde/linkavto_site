import { Fragment } from 'react'
import { Link } from 'react-router'
import { cn } from '@/shared/lib/cn'

export interface Crumb {
  label: string
  to?: string
}

export function Breadcrumbs({
  items,
  /** Полоса цвета транспорта — навигационная айдентика (§3.1). */
  accentClassName,
  className,
}: {
  items: Crumb[]
  accentClassName?: string
  className?: string
}) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Хлебные крошки" className={cn('flex items-center gap-3', className)}>
      {accentClassName ? <span aria-hidden="true" className={cn('h-4 w-1 rounded-pill', accentClassName)} /> : null}
      <ol className="no-scrollbar flex min-w-0 items-center gap-2 overflow-x-auto text-sm text-ink-muted">
        {items.map((item, index) => (
          <Fragment key={`${item.label}-${index}`}>
            {index > 0 ? (
              <li aria-hidden="true" className="text-line">
                /
              </li>
            ) : null}
            <li className="whitespace-nowrap">
              {item.to ? (
                <Link to={item.to} className="transition-colors duration-[--duration-fast] hover:text-ink">
                  {item.label}
                </Link>
              ) : (
                <span className="text-ink">{item.label}</span>
              )}
            </li>
          </Fragment>
        ))}
      </ol>
    </nav>
  )
}
