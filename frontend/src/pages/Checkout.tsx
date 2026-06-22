import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCartStore } from '../store/cartStore'

function fmt(p: number) {
  return Math.round(p).toLocaleString('ru-RU').replace(/,/g, ' ')
}

export default function Checkout() {
  const { items, totalPrice, load } = useCartStore()
  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="mx-auto max-w-[1140px] px-3 py-8">
      <h1 className="mb-6 text-2xl font-bold text-ink">Оформление заказа</h1>
      <div className="grid grid-cols-[1fr_320px] gap-6 max-md:grid-cols-1">
        <form className="flex flex-col gap-4 rounded-xl border border-gray-100 p-5">
          <h2 className="text-lg font-semibold">Контактные данные</h2>
          <input className="rounded-lg border border-gray-300 px-4 py-2.5" placeholder="ФИО" />
          <input className="rounded-lg border border-gray-300 px-4 py-2.5" placeholder="Телефон" />
          <input className="rounded-lg border border-gray-300 px-4 py-2.5" placeholder="Email" />
          <h2 className="mt-2 text-lg font-semibold">Доставка</h2>
          <input className="rounded-lg border border-gray-300 px-4 py-2.5" placeholder="Город, адрес" />
          <p className="text-sm text-gray-500">
            * Оформление заказа подключат бэкенд-разработчики (API заказа).
          </p>
        </form>

        <div className="h-fit rounded-xl border border-gray-100 p-5">
          <h2 className="mb-3 text-lg font-semibold">Ваш заказ</h2>
          {items.map((i) => (
            <div key={i.product.id} className="mb-2 flex justify-between text-sm">
              <span className="mr-2 line-clamp-1 text-gray-600">{i.product.name}</span>
              <span className="shrink-0">{i.quantity}×{fmt(i.price)}</span>
            </div>
          ))}
          <div className="mt-4 flex justify-between border-t pt-3 text-lg font-bold text-ink">
            <span>Итого</span>
            <span>{fmt(totalPrice)} ₽</span>
          </div>
          <button className="mt-4 w-full rounded-xl bg-black px-6 py-3 font-semibold text-white">
            Подтвердить заказ
          </button>
          <Link to="/cart" className="mt-2 block text-center text-sm text-gray-500 no-underline">
            Вернуться в корзину
          </Link>
        </div>
      </div>
    </div>
  )
}
