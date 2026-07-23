import { useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import type { Order } from '@/shared/api/types'
import { get } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { formatDate } from '@/shared/lib/format'
import { Badge, ErrorState, Img, Price, Skeleton } from '@/shared/ui'

export function Component() {
  const { id = '' } = useParams()
  const order = useQuery({
    queryKey: queryKeys.orders.detail(id),
    queryFn: () => get<Order>(`orders/${id}/`),
  })

  if (order.isPending) return <Skeleton className="h-64 rounded-card" />
  if (order.isError) return <ErrorState onRetry={() => void order.refetch()} />

  const data = order.data

  return (
    <section className="flex flex-col gap-4 rounded-card bg-surface p-4 shadow-float lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-mono text-md">
          {t('profile.orderNumber')} {data.number}
        </h2>
        <Badge tone={data.status === 'done' ? 'ok' : 'neutral'}>{data.status_display}</Badge>
      </div>

      <p className="text-sm text-ink-muted">{formatDate(data.created_at)}</p>

      <ul className="flex flex-col gap-3">
        {data.items.map((item) => (
          <li key={item.id} className="flex gap-3">
            <Img
              src={item.product.image?.thumb}
              alt={item.product.image?.alt ?? item.product.name}
              width={64}
              height={64}
              className="h-16 w-16 rounded-control"
            />
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="line-clamp-2 text-base">{item.product.name}</span>
              <span className="font-mono text-xs text-ink-muted">{item.product.sku}</span>
            </div>
            <span className="shrink-0 text-base tabular-nums">
              {item.quantity} × <Price value={item.price} size="sm" />
            </span>
          </li>
        ))}
      </ul>

      <div className="flex items-baseline justify-between border-t border-line pt-3">
        <span className="text-md font-semibold">{t('cart.total')}</span>
        <Price value={data.total} size="lg" />
      </div>
    </section>
  )
}
