import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import type { Banner } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { fetchBanners } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { usePrefersReducedMotion } from '@/shared/lib/media'
import { Img, Skeleton } from '@/shared/ui'

const AUTOPLAY_MS = 6000

/**
 * §4б зона 1: карусель рекламных баннеров во всю ширину; шапка плавает поверх.
 * Первый баннер — LCP (priority). Автосмена ~6с с паузой при hover,
 * уважает prefers-reduced-motion (§11). Метка «Реклама» и точки-пагинация.
 */
export function PromoCarousel() {
  const banners = useQuery({ queryKey: queryKeys.home.banners(), queryFn: fetchBanners })
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const reduced = usePrefersReducedMotion()
  const timer = useRef<number | null>(null)

  const items = banners.data ?? []
  const count = items.length

  useEffect(() => {
    if (reduced || paused || count <= 1) return
    timer.current = window.setInterval(() => setIndex((i) => (i + 1) % count), AUTOPLAY_MS)
    return () => {
      if (timer.current) window.clearInterval(timer.current)
    }
  }, [reduced, paused, count])

  if (banners.isPending) {
    return <Skeleton className="h-80 w-full rounded-none lg:h-[57rem]" />
  }

  if (count === 0) return null

  const active = index % count

  return (
    <section
      aria-roledescription="carousel"
      aria-label={t('home.promo')}
      className="relative h-80 w-full overflow-hidden lg:h-[57rem]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {items.map((banner, i) => (
        <BannerSlide key={banner.id} banner={banner} active={i === active} priority={i === 0} />
      ))}

      {/* Метка «Реклама» (§4б). */}
      <span className="absolute bottom-6 left-8 rounded-pill bg-ink/55 px-2.5 py-1 text-xs text-white">
        {t('home.adLabel')}
      </span>

      {count > 1 ? (
        <div className="absolute bottom-6 left-1/2 flex -translate-x-1/2 gap-1.5" role="tablist">
          {items.map((banner, i) => (
            <button
              key={banner.id}
              type="button"
              role="tab"
              aria-selected={i === active}
              aria-label={`${t('home.promoSlide')} ${i + 1}`}
              onClick={() => setIndex(i)}
              className={cn(
                'h-1.5 rounded-pill transition-[width,background-color] duration-[--duration-base]',
                i === active ? 'w-5 bg-white' : 'w-1.5 bg-white/50',
              )}
            />
          ))}
        </div>
      ) : null}
    </section>
  )
}

function BannerSlide({
  banner,
  active,
  priority,
}: {
  banner: Banner
  active: boolean
  priority: boolean
}) {
  return (
    <Link
      to={banner.url}
      aria-hidden={!active}
      tabIndex={active ? 0 : -1}
      className={cn(
        'absolute inset-0 transition-opacity duration-[--duration-base]',
        active ? 'opacity-100' : 'pointer-events-none opacity-0',
      )}
    >
      {banner.image?.full ? (
        <Img
          src={banner.image.full}
          alt={banner.image.alt ?? banner.title}
          width={1360}
          height={320}
          priority={priority}
          className="h-full w-full !object-cover outline-none"
        />
      ) : (
        <span className="placeholder-stripe flex h-full w-full items-end p-8">
          <span className="max-w-[24ch] text-lg font-medium text-ink lg:text-xl">{banner.title}</span>
        </span>
      )}
    </Link>
  )
}
