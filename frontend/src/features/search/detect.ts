import type { SearchMode } from '@/shared/api/types'

const VIN_RE = /^[A-HJ-NPR-Z0-9]{17}$/i
const SKU_RE = /^[A-Z0-9\-.\\/]{4,}$/i

/**
 * §7: детект типа ввода на фронте.
 * 17 символов → VIN; цифро-буквенный код без пробелов → артикул; иначе текст.
 */
export function detectSearchMode(raw: string): Exclude<SearchMode, 'auto'> {
  const value = raw.trim()
  if (VIN_RE.test(value)) return 'vin'
  if (!/\s/.test(value) && SKU_RE.test(value) && /\d/.test(value)) return 'sku'
  return 'text'
}

export function isValidVin(raw: string): boolean {
  return VIN_RE.test(raw.trim())
}
