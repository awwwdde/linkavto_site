import { useEffect, useState } from 'react'
import { useSearchParams, useParams } from 'react-router-dom'
import { getProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'

interface ProductPage {
  count: number
  page: number
  num_pages: number
  results: Product[]
}

export default function Catalog() {
  const [params, setParams] = useSearchParams()
  const { slug } = useParams()
  const search = params.get('search') ?? ''
  const category = slug ?? params.get('category') ?? ''
  const page = Number(params.get('page') ?? 1)
  const ordering = params.get('ordering') ?? ''

  const [data, setData] = useState<ProductPage | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    getProducts({ search, category, page, ordering })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [search, category, page, ordering])

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  return (
    <div className="mx-auto max-w-[1520px] px-4 py-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">
          {search ? `Результаты: «${search}»` : 'Каталог'}
          {data && <span className="ml-2 text-base font-normal text-gray-500">{data.count} товаров</span>}
        </h1>
        <select
          value={ordering}
          onChange={(e) => setParam('ordering', e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">По умолчанию</option>
          <option value="price">Цена ↑</option>
          <option value="-price">Цена ↓</option>
          <option value="name">Название А-Я</option>
          <option value="-created_at">Сначала новые</option>
        </select>
      </div>

      {loading && <p className="text-gray-500">Загрузка…</p>}

      {data && data.results.length === 0 && !loading && (
        <p className="text-gray-500">Ничего не найдено.</p>
      )}

      <div className="grid grid-cols-5 gap-3 max-xl:grid-cols-4 max-lg:grid-cols-3 max-md:grid-cols-2">
        {data?.results.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>

      {data && data.num_pages > 1 && (
        <div className="mt-8 flex justify-center gap-2">
          {Array.from({ length: data.num_pages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setParam('page', String(p))}
              className={`h-9 w-9 rounded-lg border text-sm ${
                p === page ? 'border-catalog bg-catalog text-black' : 'border-gray-300 bg-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
