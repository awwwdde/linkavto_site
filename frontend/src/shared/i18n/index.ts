import { ru, type TranslationKey } from './ru'

/**
 * §17: i18n-ready слой. Сейчас словарь один, но обращение к строкам
 * идёт только через t() — подключение второго языка не трогает компоненты.
 */
const dictionary: Record<TranslationKey, string> = ru

export function t(key: TranslationKey): string {
  return dictionary[key]
}

export type { TranslationKey }
