import { Link } from 'react-router-dom'
import { useState } from 'react'
import type { Product } from '../api'

function fmt(p: string | number | null) {
  if (p == null) return ''
  return Math.round(Number(p)).toLocaleString('ru-RU').replace(/,/g, ' ')
}

function words(s: string, n: number) {
  const parts = s.split(/\s+/)
  return parts.length > n ? parts.slice(0, n).join(' ') + '…' : s
}

export default function ProductCardCompact({ product }: { product: Product }) {
  const [fav, setFav] = useState(false)
  const hasOld = product.old_price && Number(product.old_price) > Number(product.price)

  return (
    <div className="relative flex h-full flex-col rounded-xl border border-[#f0f0f0] bg-white transition-all duration-300">
      <Link to={`/product/${product.slug}`} className="no-underline">
        <div className="relative flex h-40 items-center justify-center overflow-hidden rounded-lg">
          {product.image ? (
            <img src={product.image} alt={product.name} className="max-h-full max-w-full object-contain" />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              <i className="bi bi-image text-5xl opacity-30" />
            </div>
          )}
          <div className="absolute left-1 top-1 flex flex-col gap-1">
            {product.is_new && (
              <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[0.7rem] font-medium text-white">NEW</span>
            )}
            {product.is_original && (
              <span className="rounded bg-amber-400 px-1.5 py-0.5 text-[0.7rem] font-medium text-black">
                <i className="fas fa-certificate mr-1" />ОРИГИНАЛ
              </span>
            )}
          </div>
        </div>
      </Link>

      <button
        onClick={() => setFav((v) => !v)}
        className="absolute right-1 top-1 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-white/90"
        aria-label="В избранное"
      >
        <i className={`${fav ? 'fas fa-heart text-red-500' : 'far fa-heart text-gray-500'} text-[0.9rem]`} />
      </button>

      <div className="mt-2 p-2">
        <div className="mb-2">
          <div className="flex items-center justify-between">
            <div className="text-base font-bold text-[#89BEE8]">{fmt(product.price)} ₽</div>
            {hasOld && <span className="ml-2 text-[0.7rem] font-semibold text-red-600">-{product.discount}%</span>}
          </div>
          {hasOld && (
            <div className="text-[0.75rem] text-gray-500 line-through">{fmt(product.old_price)} ₽</div>
          )}
        </div>

        <h6 className="mb-1 h-[2.4rem] overflow-hidden text-[0.8rem] leading-[1.2]">
          <Link to={`/product/${product.slug}`} className="text-ink no-underline hover:text-[#89BEE8]">
            {words(product.name, 6)}
          </Link>
        </h6>

        <div className="mb-1 h-6">
          {product.review_count > 0 ? (
            <div className="flex items-center">
              <span className="mr-1 text-[0.85rem] font-bold text-ink">{product.average_rating.toFixed(1)}</span>
              <i className="fas fa-star mr-1 text-[0.8rem] text-amber-400" />
              <small className="text-[0.8rem] text-gray-500">{product.review_count} отзывов</small>
            </div>
          ) : (
            <div className="text-[0.8rem] text-gray-500">Нет отзывов</div>
          )}
        </div>

        <div className="mb-2">
          {product.stock > 10 ? (
            <span className="rounded bg-green-600 px-1.5 py-0.5 text-[0.65rem] text-white">В наличии</span>
          ) : product.stock > 0 ? (
            <span className="rounded bg-amber-400 px-1.5 py-0.5 text-[0.65rem] text-black">{product.stock} шт.</span>
          ) : (
            <span className="rounded bg-gray-500 px-1.5 py-0.5 text-[0.65rem] text-white">Нет</span>
          )}
        </div>
      </div>
    </div>
  )
}
