import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCartStore } from '../store/cartStore'

function fmt(p: number) {
  return Math.round(p).toLocaleString('ru-RU').replace(/,/g, ' ')
}

export default function Cart() {
  const { items, totalPrice, totalQuantity, load, add, remove, clear } = useCartStore()

  useEffect(() => {
    load()
  }, [load])

  if (!items.length) {
    return (
      <div className="mx-auto max-w-[1140px] px-3 py-16 text-center">
        <i className="bi bi-cart3 text-6xl text-gray-300" />
        <h1 className="mt-4 text-2xl font-bold text-ink">Корзина пуста</h1>
        <Link to="/catalog" className="mt-4 inline-block rounded-xl bg-black px-6 py-3 font-semibold text-white no-underline">
          В каталог
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[1140px] px-3 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Корзина</h1>
        <button onClick={() => clear()} className="text-sm text-gray-500 hover:text-red-600">
          Очистить
        </button>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-6 max-md:grid-cols-1">
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <div key={item.product.id} className="flex items-center gap-4 rounded-xl border border-gray-100 p-3">
              <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-gray-50">
                {item.product.image ? (
                  <img src={item.product.image} alt={item.product.name} className="max-h-full max-w-full object-contain" />
                ) : (
                  <i className="bi bi-image text-2xl text-gray-300" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <Link to={`/product/${item.product.slug}`} className="line-clamp-2 text-sm font-medium text-ink no-underline">
                  {item.product.name}
                </Link>
                <div className="mt-1 text-sm text-gray-500">{fmt(item.price)} ₽ / шт</div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => (item.quantity > 1 ? add(item.product.id, -1) : remove(item.product.id))}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-300"
                >
                  −
                </button>
                <span className="w-6 text-center">{item.quantity}</span>
                <button
                  onClick={() => add(item.product.id, 1)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-300"
                >
                  +
                </button>
              </div>
              <div className="w-24 text-right font-bold text-ink">{fmt(item.total_price)} ₽</div>
              <button onClick={() => remove(item.product.id)} className="text-gray-400 hover:text-red-600">
                <i className="bi bi-trash" />
              </button>
            </div>
          ))}
        </div>

        <div className="h-fit rounded-xl border border-gray-100 p-5">
          <div className="mb-2 flex justify-between text-sm text-gray-600">
            <span>Товаров</span>
            <span>{totalQuantity} шт</span>
          </div>
          <div className="mb-4 flex justify-between text-lg font-bold text-ink">
            <span>Итого</span>
            <span>{fmt(totalPrice)} ₽</span>
          </div>
          <Link
            to="/checkout"
            className="flex w-full items-center justify-center rounded-xl bg-black px-6 py-3 font-semibold text-white no-underline"
          >
            Оформить заказ
          </Link>
        </div>
      </div>
    </div>
  )
}
