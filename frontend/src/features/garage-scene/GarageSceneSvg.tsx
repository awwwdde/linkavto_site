import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'

/**
 * §4а: пререндеренный SVG той же фасеточной модели — фолбэк для mobile,
 * слабых устройств, prefers-reduced-motion и отсутствия WebGL.
 * Палитра — оттенки цвета типа транспорта, стёкла светлее, низ темнее.
 */
export function GarageSceneSvg({
  highlightZone,
  className,
}: {
  highlightZone?: string | null
  className?: string
}) {
  const lit = (zone: string) => (highlightZone === zone ? 'brightness-115' : '')

  return (
    <svg
      viewBox="0 0 480 260"
      role="img"
      aria-label={t('garage.sceneFallback')}
      className={cn('h-auto w-full', className)}
    >
      {/* «Подиум» вместо настоящей тени */}
      <ellipse cx="240" cy="222" rx="176" ry="20" fill="var(--color-env-shadow)" />

      {/* Кузов — низкополигональные грани */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('body'))}>
        <polygon points="72,186 116,140 214,128 300,132 372,152 414,186" fill="#378ADD" />
        <polygon points="72,186 414,186 402,208 84,208" fill="#185FA5" />
        <polygon points="116,140 214,128 208,110 148,116" fill="#85B7EB" />
        <polygon points="214,128 300,132 296,110 208,110" fill="#B5D4F4" />
        <polygon points="300,132 372,152 342,116 296,110" fill="#85B7EB" />
      </g>

      {/* Стёкла */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('electrics'))}>
        <polygon points="156,120 206,114 206,132 148,136" fill="#EAF3FB" />
        <polygon points="212,114 292,114 296,132 212,132" fill="#DCEAF8" />
        <polygon points="298,116 334,120 350,140 300,132" fill="#EAF3FB" />
      </g>

      {/* Капот и двигатель под ним */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('engine'))}>
        <polygon points="72,186 116,140 148,136 120,186" fill="#2E7ACB" />
      </g>

      {/* Фильтры — вставка на капоте */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('filters'))}>
        <polygon points="122,150 152,146 150,160 124,162" fill="#0C447C" opacity="0.35" />
      </g>

      {/* Колёса и подвеска */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('suspension'))}>
        <circle cx="140" cy="196" r="30" fill="#0C447C" />
        <circle cx="140" cy="196" r="15" fill="#B5D4F4" />
        <circle cx="348" cy="196" r="30" fill="#0C447C" />
        <circle cx="348" cy="196" r="15" fill="#B5D4F4" />
      </g>

      {/* Тормозные диски */}
      <g className={cn('transition-[filter] duration-[--duration-base]', lit('brakes'))}>
        <circle cx="140" cy="196" r="9" fill="#185FA5" />
        <circle cx="348" cy="196" r="9" fill="#185FA5" />
      </g>
    </svg>
  )
}
