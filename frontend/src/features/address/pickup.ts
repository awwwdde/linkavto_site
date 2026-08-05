import type { PickupProvider } from '@/shared/api/types'

/**
 * Пункты выдачи. TODO(api): реально приходят от служб доставки + выбираются на
 * карте (`accounts/address_map_modal`, Яндекс.Карты). Здесь — мок-список для
 * выбора без карты; интерактивная карта подключается отдельным SDK.
 */
export const PICKUP_PROVIDERS: { value: PickupProvider; label: string }[] = [
  { value: 'cdek', label: 'СДЭК' },
  { value: 'boxberry', label: 'Boxberry' },
  { value: 'post', label: 'Почта России' },
  { value: 'yandex', label: 'Яндекс Доставка' },
]

export const PROVIDER_LABEL: Record<PickupProvider, string> = Object.fromEntries(
  PICKUP_PROVIDERS.map((p) => [p.value, p.label]),
) as Record<PickupProvider, string>

const POINTS: Record<PickupProvider, string[]> = {
  cdek: ['ул. Тверская, 12 — ежедневно 10:00–21:00', 'Ленинградский пр-т, 80 — пн–сб 09:00–20:00'],
  boxberry: ['ул. Арбат, 24 — ежедневно 10:00–22:00', 'Кутузовский пр-т, 30 — пн–пт 10:00–19:00'],
  post: ['Отделение 101000 — Мясницкая ул., 26', 'Отделение 119021 — Льва Толстого, 16'],
  yandex: ['ТЦ «Авиапарк», Ходынский б-р, 4', 'Пункт на Профсоюзной, 61'],
}

export const pickupPoints = (provider: PickupProvider): string[] => POINTS[provider] ?? []
