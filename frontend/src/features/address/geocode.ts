import type { LatLng } from './TileMap'

/**
 * Геокодер адресов: подсказки при вводе и обратное геокодирование клика по
 * карте. Данные — OpenStreetMap/Nominatim: работает без ключа, отдаёт реальные
 * адреса России с координатами и индексом.
 *
 * TODO(api): при появлении ключа 2ГИС перевести на их геокодер — контракт тот
 * же (строка адреса, индекс, координаты), меняется только транспорт.
 * Если сеть недоступна, поиск падает на локальный справочник ниже — витрина на
 * моках остаётся рабочей.
 */
export interface GeoPoint extends LatLng {
  address: string
  postal: string
}

export const MOSCOW_CENTER: LatLng = { lat: 55.751, lng: 37.6175 }

const ENDPOINT = 'https://nominatim.openstreetmap.org'
const COMMON = 'format=jsonv2&addressdetails=1&accept-language=ru'

/** Резервный справочник — используется, когда геокодер недоступен. */
const FALLBACK: GeoPoint[] = [
  { address: 'Москва, ул. Тверская, 12', postal: '125009', lat: 55.7644, lng: 37.6062 },
  { address: 'Москва, Ленинградский пр-т, 80', postal: '125190', lat: 55.806, lng: 37.514 },
  { address: 'Москва, ул. Мясницкая, 26', postal: '101000', lat: 55.7686, lng: 37.6386 },
  { address: 'Москва, ул. Льва Толстого, 16', postal: '119021', lat: 55.734, lng: 37.5876 },
  { address: 'Москва, Кутузовский пр-т, 30', postal: '121165', lat: 55.7404, lng: 37.535 },
  { address: 'Москва, ул. Арбат, 24', postal: '119002', lat: 55.7498, lng: 37.591 },
  { address: 'Москва, Профсоюзная ул., 61', postal: '117420', lat: 55.6636, lng: 37.534 },
  { address: 'Москва, Ходынский б-р, 4', postal: '125252', lat: 55.7898, lng: 37.532 },
  { address: 'Москва, Щёлковское ш., 100', postal: '105523', lat: 55.8143, lng: 37.818 },
  { address: 'Москва, Волоколамское ш., 15', postal: '125080', lat: 55.8036, lng: 37.506 },
]

interface NominatimAddress {
  road?: string
  house_number?: string
  city?: string
  town?: string
  village?: string
  municipality?: string
  county?: string
  state?: string
  suburb?: string
  postcode?: string
}

/** «городской округ Казань» → «Казань»: в подсказке нужен только город. */
const cleanCity = (value?: string) =>
  value?.replace(/^(городской округ|муниципальный район|городское поселение|район)\s+/i, '').trim()

interface NominatimPlace {
  lat: string
  lon: string
  display_name?: string
  address?: NominatimAddress
}

/** Короткая строка «Город, улица, дом» вместо длинного display_name. */
function formatAddress(place: NominatimPlace): string {
  const a = place.address ?? {}
  const city =
    cleanCity(a.city) ?? cleanCity(a.town) ?? cleanCity(a.village) ?? cleanCity(a.municipality) ?? cleanCity(a.county) ?? a.state
  const street = [a.road, a.house_number].filter(Boolean).join(', ')
  const short = [city, street || a.suburb].filter(Boolean).join(', ')
  return short || place.display_name?.split(',').slice(0, 3).join(',') || ''
}

const toGeoPoint = (place: NominatimPlace): GeoPoint => ({
  address: formatAddress(place),
  postal: place.address?.postcode ?? '',
  lat: Number(place.lat),
  lng: Number(place.lon),
})

const localMatches = (query: string): GeoPoint[] => {
  const value = query.trim().toLowerCase()
  return FALLBACK.filter((point) => point.address.toLowerCase().includes(value)).slice(0, 6)
}

/** Подсказки по вводу. Пустой массив — ничего не нашли. */
export async function searchAddress(query: string, signal?: AbortSignal): Promise<GeoPoint[]> {
  const value = query.trim()
  if (value.length < 3) return []
  try {
    const response = await fetch(
      `${ENDPOINT}/search?${COMMON}&limit=6&countrycodes=ru&q=${encodeURIComponent(value)}`,
      { signal },
    )
    if (!response.ok) throw new Error(String(response.status))
    const places = (await response.json()) as NominatimPlace[]
    // Геокодер отдаёт и здание, и объекты внутри него — после сокращения строки
    // они выглядят одинаково, поэтому оставляем по одному адресу.
    const unique = new Map<string, GeoPoint>()
    for (const place of places) {
      const point = toGeoPoint(place)
      if (point.address && !unique.has(point.address)) unique.set(point.address, point)
    }
    const points = [...unique.values()]
    return points.length > 0 ? points : localMatches(value)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    return localMatches(value)
  }
}

/** Обратное геокодирование: что находится в точке клика по карте. */
export async function reverseGeocode(position: LatLng, signal?: AbortSignal): Promise<GeoPoint | null> {
  try {
    const response = await fetch(
      `${ENDPOINT}/reverse?${COMMON}&zoom=18&lat=${position.lat}&lon=${position.lng}`,
      { signal },
    )
    if (!response.ok) throw new Error(String(response.status))
    const place = (await response.json()) as NominatimPlace
    const point = toGeoPoint(place)
    return point.address ? { ...point, lat: position.lat, lng: position.lng } : null
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    return nearestFallback(position)
  }
}

/** Ближайший адрес локального справочника — запасной вариант без сети. */
function nearestFallback(position: LatLng): GeoPoint {
  let best = FALLBACK[0]!
  let bestDistance = Number.POSITIVE_INFINITY
  for (const point of FALLBACK) {
    // Плоское приближение — на масштабе города погрешность несущественна.
    const dx = (point.lng - position.lng) * Math.cos((position.lat * Math.PI) / 180)
    const dy = point.lat - position.lat
    const distance = dx * dx + dy * dy
    if (distance < bestDistance) {
      bestDistance = distance
      best = point
    }
  }
  return best
}

/** Точка на карте для уже сохранённого адреса — чтобы метка встала на место. */
export function pointForAddress(address: string): GeoPoint | null {
  const value = address.trim().toLowerCase()
  if (!value) return null
  return FALLBACK.find((point) => point.address.toLowerCase() === value) ?? null
}
