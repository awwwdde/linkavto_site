import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useCartStore } from '../store/cartStore'
import { getCategories, type Category } from '../api'

export default function Header() {
  const [query, setQuery] = useState('')
  const [catOpen, setCatOpen] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const navigate = useNavigate()
  const catRef = useRef<HTMLDivElement>(null)
  const totalQuantity = useCartStore((s) => s.totalQuantity)
  const loadCart = useCartStore((s) => s.load)

  useEffect(() => {
    loadCart()
    getCategories('root').then(setCategories).catch(console.error)
  }, [loadCart])

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (catRef.current && !catRef.current.contains(e.target as Node)) setCatOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate(`/catalog?search=${encodeURIComponent(query)}`)
  }

  const iconBtn = 'flex h-12 w-12 items-center justify-center rounded-xl bg-catalog text-xl text-black no-underline'

  return (
    <>
      <header className="sticky top-0 z-50 bg-header py-3">
        <div className="mx-auto flex max-w-[1520px] items-center gap-3 px-4">
          {/* Логотип */}
          <Link to="/" className="flex shrink-0 items-center no-underline">
            <img src="/static/img/Logo colored.svg" alt="LINKAVTO" className="h-7 w-[180px] object-contain" />
          </Link>

          {/* Кнопка Каталог + выпадающее меню */}
          <div className="relative shrink-0" ref={catRef}>
            <button
              onClick={() => setCatOpen((v) => !v)}
              className="flex h-12 items-center gap-2 rounded-[15px] bg-catalog px-6 text-sm font-medium text-black"
            >
              <i className="bi bi-list text-lg" />
              Каталог
            </button>
            {catOpen && (
              <div className="absolute left-0 top-[calc(100%+8px)] z-50 max-h-[70vh] w-[320px] overflow-auto rounded-xl border border-gray-200 bg-white py-2 shadow-xl">
                {categories.length === 0 && <div className="px-4 py-2 text-sm text-gray-400">Загрузка…</div>}
                {categories.map((c) => (
                  <Link
                    key={c.id}
                    to={`/category/${c.slug}`}
                    onClick={() => setCatOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-ink no-underline hover:bg-gray-50"
                  >
                    {c.icon ? <i className={c.icon} /> : <i className="bi bi-tag" />}
                    {c.name}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Поиск */}
          <form onSubmit={submit} className="relative flex-1">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              type="text"
              placeholder="Поиск по названию, VIN или марке"
              className="h-12 w-full rounded-xl border border-[#dee2e6] bg-white px-4 pr-12 text-sm outline-none focus:border-[#3498db]"
            />
            <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2 text-xl text-gray-700">
              <i className="bi bi-search" />
            </button>
          </form>

          {/* Иконки справа */}
          <div className="flex shrink-0 items-center gap-2">
            <button onClick={() => setCatOpen((v) => !v)} className={iconBtn} aria-label="Каталог">
              <i className="bi bi-grid" />
            </button>
            <Link to="/favorites" className={iconBtn} aria-label="Избранное">
              <i className="bi bi-heart" />
            </Link>
            <Link to="/cart" className={`relative ${iconBtn}`} aria-label="Корзина">
              <i className="bi bi-cart3" />
              {totalQuantity > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[11px] font-bold text-white">
                  {totalQuantity}
                </span>
              )}
            </Link>
            <Link to="/account" className={iconBtn} aria-label="Профиль">
              <i className="bi bi-person" />
            </Link>
          </div>
        </div>
      </header>

      {/* Полоса «Указать адрес» / «Стать продавцом» */}
      <div className="border-b bg-white">
        <div className="mx-auto flex max-w-[1520px] justify-end gap-2 px-4 py-2">
          <button className="flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-ink hover:bg-gray-50">
            <i className="bi bi-geo-alt" />
            Указать адрес
          </button>
          <Link
            to="/sellers/become"
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-ink no-underline hover:bg-gray-50"
          >
            Стать продавцом
          </Link>
        </div>
      </div>
    </>
  )
}
