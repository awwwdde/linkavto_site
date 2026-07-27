import { useState } from 'react'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconPhoto } from './Icon'

export interface ImgProps {
  src: string | null | undefined
  alt: string
  /** Обязательны — иначе CLS (§12). */
  width: number
  height: number
  /** LCP-картинка: грузится сразу и с высоким приоритетом. */
  priority?: boolean
  srcSet?: string
  sizes?: string
  className?: string
  wrapperClassName?: string
  /**
   * Заполнять контейнер с обрезкой (object-cover), для карточек, где фото
   * флешит к краям. По умолчанию object-contain (§3.3 — показать деталь целиком
   * на белом с тонкой обводкой, чтобы не сливалась с карточкой).
   */
  cover?: boolean
}

export function Img({
  src,
  alt,
  width,
  height,
  priority = false,
  srcSet,
  sizes,
  className,
  wrapperClassName,
  cover = false,
}: ImgProps) {
  const [failed, setFailed] = useState(false)

  if (!src || failed) {
    return (
      <span
        className={cn(
          'flex items-center justify-center rounded-control bg-paper text-ink-muted',
          wrapperClassName,
          className,
        )}
        style={{ aspectRatio: `${width} / ${height}` }}
        role="img"
        aria-label={t('common.noPhoto')}
      >
        <IconPhoto width={28} height={28} />
      </span>
    )
  }

  return (
    <img
      src={src}
      srcSet={srcSet}
      sizes={sizes}
      alt={alt}
      width={width}
      height={height}
      loading={priority ? 'eager' : 'lazy'}
      decoding={priority ? 'sync' : 'async'}
      fetchPriority={priority ? 'high' : 'auto'}
      onError={() => setFailed(true)}
      // Белое фото не должно сливаться с карточкой (§3.3) — тонкая обводка в
      // режиме contain; в режиме cover фото само доходит до краёв, обводка не нужна.
      className={cn(
        cover ? 'object-cover' : 'object-contain outline outline-1 -outline-offset-1 outline-ink/8',
        className,
      )}
    />
  )
}
