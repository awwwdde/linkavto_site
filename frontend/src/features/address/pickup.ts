import type { PickupProvider } from '@/shared/api/types'

/**
 * Пункты выдачи для самовывоза. В выдаче участвуют только Почта России и СДЭК;
 * лейблы остальных служб оставлены для адресов, сохранённых раньше.
 *
 * TODO(api): точки приходят от служб доставки (`delivery/pickup-points/`) с
 * реальными координатами. Здесь — мок-справочник с координатами в процентах
 * полотна карты (0…100), чтобы метки раскладывались без внешних запросов.
 */
export const PICKUP_PROVIDERS: { value: PickupProvider; label: string; short: string }[] = [
  { value: 'post', label: 'Почта России', short: 'ПОЧТА' },
  { value: 'cdek', label: 'СДЭК', short: 'СДЭК' },
]

export const DEFAULT_PICKUP_PROVIDER: PickupProvider = 'post'

export const PROVIDER_LABEL: Record<PickupProvider, string> = {
  post: 'Почта России',
  cdek: 'СДЭК',
  boxberry: 'Boxberry',
  yandex: 'Яндекс Доставка',
}

export interface PickupPoint {
  provider: PickupProvider
  /** Короткое имя пункта — оно же сохраняется в адресе. */
  name: string
  address: string
  schedule: string
  lat: number
  lng: number
}

const POINTS: PickupPoint[] = [
  { provider: 'post', name: 'Отделение 101000', address: 'Мясницкая ул., 26', schedule: 'пн–пт 09:00–20:00, сб 09:00–18:00', lat: 55.7686, lng: 37.6386 },
  { provider: 'post', name: 'Отделение 119021', address: 'ул. Льва Толстого, 16', schedule: 'пн–пт 09:00–19:00', lat: 55.734, lng: 37.5876 },
  { provider: 'post', name: 'Отделение 125009', address: 'ул. Тверская, 12', schedule: 'ежедневно 08:00–20:00', lat: 55.7644, lng: 37.6062 },
  { provider: 'post', name: 'Отделение 117420', address: 'Профсоюзная ул., 61', schedule: 'пн–сб 09:00–19:00', lat: 55.6636, lng: 37.534 },
  { provider: 'post', name: 'Отделение 125080', address: 'Волоколамское ш., 15', schedule: 'пн–пт 09:00–19:00', lat: 55.8036, lng: 37.506 },
  { provider: 'post', name: 'Отделение 105523', address: 'Щёлковское ш., 100', schedule: 'пн–сб 09:00–20:00', lat: 55.8143, lng: 37.818 },
  { provider: 'post', name: 'Отделение 119048', address: 'Комсомольский пр-т, 42', schedule: 'пн–пт 09:00–19:00', lat: 55.7237, lng: 37.5766 },
  { provider: 'cdek', name: 'СДЭК Тверская', address: 'ул. Тверская, 12, офис 4', schedule: 'ежедневно 10:00–21:00', lat: 55.7662, lng: 37.6045 },
  { provider: 'cdek', name: 'СДЭК Ленинградский', address: 'Ленинградский пр-т, 80', schedule: 'пн–сб 09:00–20:00', lat: 55.806, lng: 37.514 },
  { provider: 'cdek', name: 'СДЭК Кутузовский', address: 'Кутузовский пр-т, 30', schedule: 'пн–пт 10:00–19:00', lat: 55.7404, lng: 37.535 },
  { provider: 'cdek', name: 'СДЭК Арбат', address: 'ул. Арбат, 24', schedule: 'ежедневно 10:00–22:00', lat: 55.7498, lng: 37.591 },
  { provider: 'cdek', name: 'СДЭК Авиапарк', address: 'Ходынский б-р, 4', schedule: 'ежедневно 10:00–22:00', lat: 55.7898, lng: 37.532 },
  { provider: 'cdek', name: 'СДЭК Автозаводская', address: 'Автозаводская ул., 18', schedule: 'пн–сб 10:00–20:00', lat: 55.708, lng: 37.657 },
]

/** Точки выбранных служб; пустой фильтр — значит показываем все. */
export function pickupPoints(providers?: PickupProvider[]): PickupPoint[] {
  if (!providers || providers.length === 0) return POINTS
  return POINTS.filter((point) => providers.includes(point.provider))
}

export const findPickupPoint = (name: string): PickupPoint | null =>
  POINTS.find((point) => point.name === name) ?? null
