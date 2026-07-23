import { useEffect, useState } from 'react'
import type { PriceHistogramBucket } from '@/shared/api/types'
import { formatPrice } from '@/shared/lib/format'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'

export interface PriceHistogramSliderProps {
  /** Копейки. */
  min: number
  max: number
  value: [number, number]
  histogram: PriceHistogramBucket[]
  onCommit: (value: [number, number]) => void
}

/** §6: слайдер цены с мини-гистограммой распределения по текущей выборке. */
export function PriceHistogramSlider({ min, max, value, histogram, onCommit }: PriceHistogramSliderProps) {
  const [local, setLocal] = useState<[number, number]>(value)

  useEffect(() => setLocal(value), [value])

  const peak = Math.max(1, ...histogram.map((bucket) => bucket.count))
  const span = Math.max(1, max - min)
  const leftPercent = ((local[0] - min) / span) * 100
  const rightPercent = ((local[1] - min) / span) * 100

  const commit = (next: [number, number]) => {
    const ordered: [number, number] = next[0] <= next[1] ? next : [next[1], next[0]]
    setLocal(ordered)
    onCommit(ordered)
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex h-12 items-end gap-0.5" aria-hidden="true">
        {histogram.map((bucket, index) => {
          const inRange = bucket.to >= local[0] && bucket.from <= local[1]
          return (
            <span
              key={index}
              className={cn('flex-1 rounded-t-[2px]', inRange ? 'bg-ink/30' : 'bg-line')}
              style={{ height: `${Math.max(4, (bucket.count / peak) * 100)}%` }}
            />
          )
        })}
      </div>

      <div className="relative h-6">
        <span className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-pill bg-line" />
        <span
          className="absolute top-1/2 h-1 -translate-y-1/2 rounded-pill bg-ink"
          style={{ left: `${leftPercent}%`, right: `${100 - rightPercent}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={100}
          value={local[0]}
          aria-label={t('catalog.priceFrom')}
          onChange={(event) => setLocal([Number(event.target.value), local[1]])}
          onPointerUp={() => commit(local)}
          onKeyUp={() => commit(local)}
          className="pointer-events-none absolute inset-x-0 top-0 h-6 w-full appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-pill [&::-webkit-slider-thumb]:border [&::-webkit-slider-thumb]:border-line [&::-webkit-slider-thumb]:bg-surface [&::-webkit-slider-thumb]:shadow-float"
        />
        <input
          type="range"
          min={min}
          max={max}
          step={100}
          value={local[1]}
          aria-label={t('catalog.priceTo')}
          onChange={(event) => setLocal([local[0], Number(event.target.value)])}
          onPointerUp={() => commit(local)}
          onKeyUp={() => commit(local)}
          className="pointer-events-none absolute inset-x-0 top-0 h-6 w-full appearance-none bg-transparent [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-pill [&::-webkit-slider-thumb]:border [&::-webkit-slider-thumb]:border-line [&::-webkit-slider-thumb]:bg-surface [&::-webkit-slider-thumb]:shadow-float"
        />
      </div>

      <p className="text-sm text-ink-muted tabular-nums">
        {t('catalog.priceFrom')} {formatPrice(local[0])} {t('catalog.priceTo')} {formatPrice(local[1])}
      </p>
    </div>
  )
}
