import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { queryKeys } from '@/shared/api/query-keys'
import { IconClose, IconSearch } from '@/shared/ui/Icon'
import { GarageChip } from '@/features/garage/GarageChip'
import { fetchSuggestions } from './api'
import { detectSearchMode } from './detect'
import { useSearchHistory } from './history'

const MODE_LABEL = {
  vin: t('search.modeVin'),
  sku: t('search.modeSku'),
  text: t('search.modeText'),
} as const

/** Популярные запросы для пустого состояния (§7). TODO(api): отдать бэком `search/popular/`. */
const POPULAR = [
  'Масляный фильтр',
  'Тормозные колодки',
  'Аккумулятор',
  'Свечи зажигания',
  'Щётки стеклоочистителя',
  'Моторное масло',
]

function useDebounced(value: string, ms: number) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), ms)
    return () => window.clearTimeout(timer)
  }, [value, ms])
  return debounced
}

export interface SmartSearchProps {
  /** Полноэкранный режим на mobile — подсказки в потоке, не в дропдауне. */
  variant?: 'inline' | 'overlay'
  autoFocus?: boolean
  showGarageChip?: boolean
  onNavigate?: () => void
  className?: string
}

export function SmartSearch({
  variant = 'inline',
  autoFocus = false,
  showGarageChip = true,
  onNavigate,
  className,
}: SmartSearchProps) {
  const navigate = useNavigate()
  const [value, setValue] = useState('')
  const [open, setOpen] = useState(variant === 'overlay')
  const containerRef = useRef<HTMLDivElement>(null)
  const debounced = useDebounced(value.trim(), 250)
  const history = useSearchHistory((state) => state.items)
  const pushHistory = useSearchHistory((state) => state.push)
  const clearHistory = useSearchHistory((state) => state.clear)

  const mode = useMemo(() => (value.trim().length >= 2 ? detectSearchMode(value) : null), [value])

  const suggestions = useQuery({
    queryKey: queryKeys.search.suggest(debounced),
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.length >= 2,
    staleTime: 60_000,
  })

  useEffect(() => {
    if (variant === 'overlay') return
    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [variant])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const query = value.trim()
    if (query.length < 2) return
    pushHistory(query)
    setOpen(false)
    onNavigate?.()
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  const goTo = (url: string, query?: string) => {
    if (query) pushHistory(query)
    setOpen(false)
    onNavigate?.()
    navigate(url)
  }

  const showPanel = open
  const items = suggestions.data ?? []

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      <form
        onSubmit={submit}
        role="search"
        className={cn(
          'flex h-12 w-full items-center gap-2 rounded-pill border border-line bg-surface pr-2 pl-4',
          'transition-[border-color] duration-[--duration-fast] focus-within:border-ink-muted',
        )}
      >
        <IconSearch className="shrink-0 text-ink-muted" />
        <input
          type="search"
          value={value}
          autoFocus={autoFocus}
          onChange={(event) => {
            setValue(event.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          placeholder={t('search.placeholder')}
          aria-label={t('search.placeholder')}
          className="h-full min-w-0 flex-1 bg-transparent text-base text-ink outline-none placeholder:text-ink-muted [&::-webkit-search-cancel-button]:hidden"
        />

        {value ? (
          <button
            type="button"
            onClick={() => setValue('')}
            aria-label={t('search.clear')}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-pill text-ink-muted hover:text-ink"
          >
            <IconClose width={18} height={18} />
          </button>
        ) : null}

        {showGarageChip ? <GarageChip className="hidden shrink-0 lg:inline-flex" /> : null}
      </form>

      {mode ? (
        <p className="sr-only" aria-live="polite">
          {MODE_LABEL[mode]}
        </p>
      ) : null}

      {showPanel ? (
        <div
          className={cn(
            'z-40 mt-2 w-full overflow-hidden rounded-card bg-surface',
            variant === 'inline' ? 'absolute top-full left-0 shadow-lift' : 'relative',
          )}
        >
          {debounced.length >= 2 ? (
            <div className="flex flex-col py-2">
              <p className="px-4 py-2 text-xs text-ink-muted">{mode ? MODE_LABEL[mode] : t('search.suggestions')}</p>
              {suggestions.isPending ? (
                <p className="px-4 py-3 text-base text-ink-muted">{t('common.loading')}…</p>
              ) : items.length === 0 ? (
                <p className="px-4 py-3 text-base text-ink-muted">{t('search.emptyTitle')}</p>
              ) : (
                items.map((item) => (
                  <Link
                    key={`${item.type}-${item.url}`}
                    to={item.url}
                    onClick={() => goTo(item.url, value)}
                    className="flex min-h-10 items-center justify-between gap-4 px-4 py-2 text-base hover:bg-paper"
                  >
                    <span className="truncate">{item.title}</span>
                    {item.subtitle ? (
                      <span className="shrink-0 font-mono text-sm text-ink-muted">{item.subtitle}</span>
                    ) : null}
                  </Link>
                ))
              )}
            </div>
          ) : (
            <div className="flex flex-col py-2">
              {history.length > 0 ? (
                <>
                  <div className="flex items-center justify-between px-4 py-2">
                    <p className="text-xs text-ink-muted">{t('search.history')}</p>
                    <button type="button" onClick={clearHistory} className="text-xs text-ink-muted hover:text-ink">
                      {t('search.historyClear')}
                    </button>
                  </div>
                  {history.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => goTo(`/search?q=${encodeURIComponent(item)}`, item)}
                      className="flex min-h-10 items-center px-4 py-2 text-left text-base hover:bg-paper"
                    >
                      {item}
                    </button>
                  ))}
                </>
              ) : null}

              <p className="px-4 py-2 text-xs text-ink-muted">{t('search.popular')}</p>
              {POPULAR.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => goTo(`/search?q=${encodeURIComponent(item)}`, item)}
                  className="flex min-h-10 items-center px-4 py-2 text-left text-base text-ink-muted hover:bg-paper hover:text-ink"
                >
                  {item}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
