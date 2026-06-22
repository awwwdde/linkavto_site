import { useEffect, useState } from 'react'
import type { CarouselSlide } from '../api'

const DEFAULT_SLIDES = [
  '/static/img/lighttechn.png',
  '/static/img/gruztechn.png',
  '/static/img/mototechn.png',
  '/static/img/spectechn.png',
  '/static/img/shintech.png',
]

export default function HeroCarousel({ slides }: { slides: CarouselSlide[] }) {
  const images = slides.length
    ? slides.map((s) => ({ src: s.image ?? '', url: s.url, title: s.title }))
    : DEFAULT_SLIDES.map((src) => ({ src, url: '', title: '' }))

  const [index, setIndex] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setIndex((i) => (i + 1) % images.length), 5000)
    return () => clearInterval(t)
  }, [images.length])

  const go = (dir: number) => setIndex((i) => (i + dir + images.length) % images.length)

  const Img = (
    <img
      src={images[index].src}
      alt={images[index].title || `Слайд ${index + 1}`}
      className="block h-[420px] w-full object-fill max-lg:h-[280px] max-md:h-[200px] max-sm:h-[130px]"
    />
  )

  return (
    <div className="relative mb-6 overflow-hidden rounded-2xl bg-[#f9fafb]">
      {images[index].url ? (
        <a href={images[index].url} target="_blank" rel="noopener noreferrer">
          {Img}
        </a>
      ) : (
        Img
      )}

      <button
        onClick={() => go(-1)}
        className="absolute left-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-slate-900/45 text-white"
        aria-label="Назад"
      >
        <i className="bi bi-chevron-left" />
      </button>
      <button
        onClick={() => go(1)}
        className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full bg-slate-900/45 text-white"
        aria-label="Вперёд"
      >
        <i className="bi bi-chevron-right" />
      </button>
    </div>
  )
}
