import type { ProductAttribute } from '@/shared/api/types'
import { t } from '@/shared/i18n'

export function AttributesTable({ attributes }: { attributes: ProductAttribute[] }) {
  if (attributes.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">{t('product.attributes')}</h2>
      <dl className="overflow-hidden rounded-card bg-surface shadow-float">
        {attributes.map((attribute, index) => (
          <div
            key={attribute.name}
            className={`flex items-baseline justify-between gap-6 px-4 py-3 ${index > 0 ? 'border-t border-line' : ''}`}
          >
            <dt className="text-base text-ink-muted">{attribute.name}</dt>
            <dd className="text-right text-base tabular-nums">{attribute.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
