import type { ProductAttribute } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { SectionHeading } from '@/app/layouts/SectionHeading'

export function AttributesTable({ attributes }: { attributes: ProductAttribute[] }) {
  if (attributes.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <SectionHeading lead={t('product.attributes')} ghost={t('product.attributesGhost')} />
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
