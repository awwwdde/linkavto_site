import { Link } from 'react-router-dom'
import { useState } from 'react'
import type { Product } from '../api'
import { useCartStore } from '../store/cartStore'

function fmt(p: string | number | null) {
  if (p == null) return ''
  return Math.round(Number(p)).toLocaleString('ru-RU').replace(/,/g, ' ')
}

export default function ProductCard({ product }: { product: Product }) {
  const [fav, setFav] = useState(false)
  const add = useCartStore((s) => s.add)
  const inCart = useCartStore((s) => s.isInCart(product.id))
  const hasOld = product.old_price && Number(product.old_price) > Number(product.price)

  const cartLabel = inCart
    ? 'В корзине'
    : product.stock > 0
      ? 'В корзину'
      : product.is_active
        ? 'Под заказ'
        : 'Нет в наличии'

  return (
    <div className="mx-auto w-full max-w-[220px]">
      <div className="relative flex h-full flex-col rounded-t-2xl border-0 pb-7">
        <Link to={`/product/${product.slug}`} className="no-underline">
          <div className="flex h-[150px] items-center justify-center overflow-hidden rounded-t-2xl">
            {product.image ? (
              <img src={product.image} alt={product.name} className="max-h-full max-w-full object-contain" />
            ) : (
              <div className="flex h-full items-center justify-center text-gray-400">
                <i className="bi bi-image text-5xl opacity-30" />
              </div>
            )}
          </div>
        </Link>

        <button
          onClick={() => setFav((v) => !v)}
          className="absolute right-2 top-0 m-2"
          aria-label="В избранное"
        >
          <i className={`${fav ? 'fas fa-heart text-red-500' : 'far fa-heart text-gray-500'}`} />
        </button>

        {product.is_original && (
          <div className="absolute left-2 top-0 m-2">
            <span className="rounded bg-amber-400 px-2 py-1 text-[0.7rem] font-semibold text-black">
              <i className="fas fa-certificate mr-1" />ОРИГИНАЛ
            </span>
          </div>
        )}

        <div className="flex h-[200px] flex-col overflow-hidden p-2">
          <div className="mb-2 h-8 text-base font-bold text-[#89BEE8]">
            {hasOld && <span className="mr-2 text-gray-400 line-through">{fmt(product.old_price)} ₽</span>}
            {fmt(product.price)} ₽
            {hasOld && <span className="ml-2 text-sm font-bold text-red-600">-{product.discount}%</span>}
          </div>

          <div className="mb-1 h-10 overflow-hidden">
            <h5 className="m-0 text-base">
              <Link to={`/product/${product.slug}`} className="line-clamp-2 text-ink no-underline">
                {product.name}
              </Link>
            </h5>
          </div>

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

          <div className="mb-2 h-6 text-sm">
            {product.stock > 10 ? (
              <span className="rounded bg-green-100 px-2 py-0.5 text-green-700">В наличии</span>
            ) : product.stock > 0 ? (
              <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-700">Осталось {product.stock} шт.</span>
            ) : product.is_active ? (
              <span className="rounded bg-sky-100 px-2 py-0.5 text-sky-700">Под заказ</span>
            ) : (
              <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-500">Нет в наличии</span>
            )}
          </div>
        </div>

        <div className="absolute bottom-0 w-full p-0">
          <button
            onClick={() => add(product.id)}
            disabled={product.stock === 0 && !product.is_active}
            className={`mx-2 mb-2 flex min-h-[38px] w-[calc(100%-16px)] items-center justify-center gap-1 rounded-xl px-0 py-2 text-[0.8rem] font-semibold transition-all ${
              inCart ? 'bg-[#c1e7ff] text-black' : 'bg-black text-white'
            }`}
          >
            <i className={`bi ${inCart ? 'bi-cart-check' : 'bi-cart3'}`} />
            <span>{cartLabel}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
