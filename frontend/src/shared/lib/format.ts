const numberRu = new Intl.NumberFormat('ru-RU')
const dateRu = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

/** Деньги в копейках → строка с валютой. */
export function formatPrice(kopecks: number, currency = '₽'): string {
  const rubles = kopecks / 100
  const formatted = new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: Number.isInteger(rubles) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(rubles)
  return `${formatted}\u00a0${currency}`
}

export function formatNumber(value: number): string {
  return numberRu.format(value)
}

/** Русское склонение: 1 товар / 2 товара / 5 товаров. */
export function formatPlural(
  count: number,
  forms: { one: string; few: string; many: string },
): string {
  const abs = Math.abs(count) % 100
  const last = abs % 10
  let form = forms.many
  if (abs < 11 || abs > 19) {
    if (last === 1) form = forms.one
    else if (last >= 2 && last <= 4) form = forms.few
  }
  return `${formatNumber(count)}\u00a0${form}`
}

export function formatDate(iso: string): string {
  return dateRu.format(new Date(iso))
}

/** Срок доставки в днях → человекочитаемая строка. */
export function formatDeliveryDays(days: number): string {
  if (days <= 0) return 'Сегодня'
  if (days === 1) return 'Завтра'
  return formatPlural(days, { one: 'день', few: 'дня', many: 'дней' })
}
