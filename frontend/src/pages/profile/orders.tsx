import { Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import type { Order, Paginated } from '@/shared/api/types'
import { get } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { formatDate } from '@/shared/lib/format'
import { Badge, ButtonLink, EmptyState, ErrorState, Price, Skeleton } from '@/shared/ui'

export function Component() {
  const orders = useQuery({
    queryKey: queryKeys.orders.list(),
    queryFn: () => get<Paginated<Order>>('orders/'),
  })

  if (orders.isPending) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 3 }, (_, index) => (
          <Skeleton key={index} className="h-24 rounded-card" />
        ))}
      </div>
    )
  }

  if (orders.isError) return <ErrorState onRetry={() => void orders.refetch()} />

  if (orders.data.results.length === 0) {
    return (
      <EmptyState
        title={t('profile.ordersEmptyTitle')}
        text={t('profile.ordersEmptyText')}
        action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
      />
    )
  }

  return (
    <ul className="flex flex-col gap-3">
      {orders.data.results.map((order) => (
        <li key={order.id}>
          <Link
            to={`/profile/orders/${order.id}`}
            className="flex items-center justify-between gap-4 rounded-card bg-surface p-4 shadow-float"
          >
            <span className="flex flex-col gap-1">
              <span className="font-mono text-base">
                {t('profile.orderNumber')} {order.number}
              </span>
              <span className="text-sm text-ink-muted">{formatDate(order.created_at)}</span>
            </span>
            <span className="flex items-center gap-3">
              <Badge tone={order.status === 'done' ? 'ok' : 'neutral'}>{order.status_display}</Badge>
              <Price value={order.total} size="sm" />
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}
