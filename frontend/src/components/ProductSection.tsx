import type { Product } from '../api'
import ProductCardCompact from './ProductCardCompact'

export default function ProductSection({ title, products }: { title: string; products: Product[] }) {
  if (!products.length) return null
  return (
    <section className="mb-8">
      <div className="mb-3">
        <h2 className="text-2xl font-bold text-ink">{title}</h2>
      </div>
      <div className="grid grid-cols-6 gap-3 max-xl:grid-cols-5 max-lg:grid-cols-4 max-md:grid-cols-3 max-sm:grid-cols-2">
        {products.map((p) => (
          <ProductCardCompact key={p.id} product={p} />
        ))}
      </div>
    </section>
  )
}
