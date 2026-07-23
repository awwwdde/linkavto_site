import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconChevronLeft, IconChevronRight } from './Icon'

export interface PaginationProps {
  page: number
  pageCount: number
  onChange: (page: number) => void
  className?: string
}

function pagesToShow(page: number, pageCount: number): (number | 'gap')[] {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, i) => i + 1)
  const pages = new Set<number>([1, pageCount, page, page - 1, page + 1])
  const sorted = [...pages].filter((p) => p >= 1 && p <= pageCount).sort((a, b) => a - b)
  const out: (number | 'gap')[] = []
  let previous = 0
  for (const value of sorted) {
    if (previous && value - previous > 1) out.push('gap')
    out.push(value)
    previous = value
  }
  return out
}

export function Pagination({ page, pageCount, onChange, className }: PaginationProps) {
  if (pageCount <= 1) return null

  const cell =
    'flex h-10 min-w-10 items-center justify-center rounded-control px-2 text-base tabular-nums transition-colors duration-[--duration-fast]'

  return (
    <nav className={cn('flex items-center justify-center gap-1', className)} aria-label={t('common.page')}>
      <button
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        aria-label={t('common.prevPage')}
        className={cn(cell, 'text-ink-muted hover:bg-ink/5 disabled:opacity-40')}
      >
        <IconChevronLeft width={18} height={18} />
      </button>

      {pagesToShow(page, pageCount).map((item, index) =>
        item === 'gap' ? (
          <span key={`gap-${index}`} className={cn(cell, 'text-ink-muted')} aria-hidden="true">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            onClick={() => onChange(item)}
            aria-current={item === page ? 'page' : undefined}
            className={cn(cell, item === page ? 'bg-ink text-white' : 'text-ink hover:bg-ink/5')}
          >
            {item}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= pageCount}
        aria-label={t('common.nextPage')}
        className={cn(cell, 'text-ink-muted hover:bg-ink/5 disabled:opacity-40')}
      >
        <IconChevronRight width={18} height={18} />
      </button>
    </nav>
  )
}
