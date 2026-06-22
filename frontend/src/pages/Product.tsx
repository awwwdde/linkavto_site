import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getProduct, type Product as P } from '../api'
import { useCartStore } from '../store/cartStore'

function fmt(p: string | number | null) {
  if (p == null) return ''
  return Math.round(Number(p)).toLocaleString('ru-RU').replace(/,/g, ' ')
}

export default function Product() {
  const { slug } = useParams()
  const [product, setProduct] = useState<P | null>(null)
  const add = useCartStore((s) => s.add)
  const items = useCartStore((s) => s.items)
  const inCart = product ? items.some((i) => i.product.id === product.id) : false

  useEffect(() => {
    if (slug) getProduct(slug).then(setProduct).catch(console.error)
  }, [slug])

  if (!product) return <div className="mx-auto max-w-[1140px] px-3 py-10 text-gray-500">Загрузка…</div>

  const hasOld = product.old_price && Number(product.old_price) > Number(product.price)

  return (
    <div className="mx-auto max-w-[1140px] px-3 py-8">
      <div className="grid grid-cols-2 gap-8 max-md:grid-cols-1">
        <div className="flex items-center justify-center rounded-2xl border border-gray-100 p-6">
          {product.image ? (
            <img src={product.image} alt={product.name} className="max-h-[420px] max-w-full object-contain" />
          ) : (
            <i className="bi bi-image text-7xl text-gray-300" />
          )}
        </div>

        <div>
          <h1 className="mb-2 text-2xl font-bold text-ink">{product.name}</h1>
          {product.part_number && (
            <p className="mb-4 text-sm text-gray-500">Артикул: {product.part_number}</p>
          )}

          <div className="mb-4 flex items-center gap-3">
            <span className="text-3xl font-bold text-[#89BEE8]">{fmt(product.price)} ₽</span>
            {hasOld && (
              <>
                <span className="text-lg text-gray-400 line-through">{fmt(product.old_price)} ₽</span>
                <span className="rounded bg-red-100 px-2 py-1 text-sm font-bold text-red-600">-{product.discount}%</span>
              </>
            )}
          </div>

          <div className="mb-4">
            {product.stock > 10 ? (
              <span className="rounded bg-green-100 px-2 py-1 text-sm text-green-700">В наличии</span>
            ) : product.stock > 0 ? (
              <span className="rounded bg-amber-100 px-2 py-1 text-sm text-amber-700">Осталось {product.stock} шт.</span>
            ) : (
              <span className="rounded bg-sky-100 px-2 py-1 text-sm text-sky-700">Под заказ</span>
            )}
          </div>

          <button
            onClick={() => add(product.id)}
            className={`mb-6 flex min-h-[44px] w-full max-w-xs items-center justify-center gap-2 rounded-xl px-6 py-3 font-semibold transition-all ${
              inCart ? 'bg-[#c1e7ff] text-black' : 'bg-black text-white'
            }`}
          >
            <i className={`bi ${inCart ? 'bi-cart-check' : 'bi-cart3'}`} />
            {inCart ? 'В корзине' : 'В корзину'}
          </button>

          {product.description && (
            <div className="prose max-w-none text-sm text-gray-700" dangerouslySetInnerHTML={{ __html: product.description }} />
          )}
        </div>
      </div>
    </div>
  )
}
