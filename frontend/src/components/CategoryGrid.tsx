import { Link } from 'react-router-dom'
import type { Category } from '../api'

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}

export default function CategoryGrid({ categories }: { categories: Category[] }) {
  return (
    <div className="grid w-4/5 grid-cols-6 gap-2.5 py-5 max-md:w-full max-md:[grid-template-columns:repeat(auto-fit,minmax(150px,1fr))]">
      {categories.map((c) => (
        <Link
          key={c.id}
          to={`/category/${c.slug}`}
          className="relative block overflow-hidden rounded-[15px] text-white no-underline shadow-[0_4px_12px_rgba(0,0,0,0.1)] transition-transform duration-300 hover:-translate-y-0.5"
        >
          {c.image ? (
            <img src={c.image} alt={c.name} loading="lazy" className="h-40 w-full rounded-[15px] object-cover" />
          ) : (
            <div className="flex h-[200px] items-center justify-center rounded-[15px] bg-[linear-gradient(135deg,#667eea_0%,#764ba2_100%)] text-center text-lg font-semibold text-white">
              {truncate(c.name, 15)}
            </div>
          )}
          <div className="absolute bottom-0 left-0 right-0 flex h-[60px] items-center justify-center rounded-b-[15px] bg-[linear-gradient(to_top,rgba(0,0,0,0.6),transparent)] px-2.5">
            <div className="text-center text-[1.1rem] font-semibold [text-shadow:0_1px_3px_rgba(0,0,0,0.8)]">
              {c.name}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
