/** Единая точка конфигурации фронта. */

export const API_BASE_URL = import.meta.env['VITE_API_BASE_URL'] ?? '/api/v1/'

export const MOCKS_ENABLED = import.meta.env['VITE_ENABLE_MOCKS'] === 'true'

/** §17: валюта — параметр, а не константа в форматтере. */
export const DEFAULT_CURRENCY = 'RUB'
export const DEFAULT_LOCALE = 'ru-RU'

/** Брейкпоинты §8. Держим здесь, чтобы JS и CSS не разъезжались. */
export const BREAKPOINTS = {
  md: 768,
  lg: 1024,
  xl: 1440,
} as const

export const PAGE_SIZE = 24

/** §17: ShareButtons — конфиг, а не хардкод. */
export const SHARE_TARGETS = [
  { id: 'vk', label: 'ВКонтакте', href: (url: string) => `https://vk.com/share.php?url=${encodeURIComponent(url)}` },
  { id: 'max', label: 'MAX', href: (url: string) => `https://max.ru/share?url=${encodeURIComponent(url)}` },
] as const

export const SITE_ORIGIN = 'https://linkavto.ru'
