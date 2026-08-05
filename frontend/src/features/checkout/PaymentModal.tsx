import { useEffect } from 'react'
import { t } from '@/shared/i18n'
import { Modal, Price } from '@/shared/ui'

/**
 * Мок-эквайер. Реальная оплата картой идёт редиректом на защищённую страницу
 * банка (карту на нашем сайте НЕ собираем — PCI/безопасность). Здесь — имитация:
 * авто-успех через ~2.2с; ссылка «отказ» — чтобы проверить сценарий payment_fail.
 * TODO(api): редирект на эквайера (T-Bank/ЮKassa) и вебхук статуса заказа.
 */
export function PaymentModal({
  open,
  method,
  amount,
  onSuccess,
  onFail,
  onClose,
}: {
  open: boolean
  method: 'card' | 'sbp'
  amount: number
  onSuccess: () => void
  onFail: () => void
  onClose: () => void
}) {
  useEffect(() => {
    if (!open) return
    const id = window.setTimeout(onSuccess, 2200)
    return () => window.clearTimeout(id)
  }, [open, onSuccess])

  return (
    <Modal open={open} onClose={onClose} title={method === 'sbp' ? t('payment.sbpTitle') : t('payment.cardTitle')}>
      <div className="flex flex-col items-center gap-4 text-center">
        {method === 'sbp' ? <QrPlaceholder /> : <Spinner />}

        <div className="flex flex-col items-center gap-1">
          <span className="text-md font-semibold">{t('payment.processing')}</span>
          <Price value={amount} size="lg" />
        </div>

        <p className="max-w-[42ch] text-sm text-ink-muted">
          {method === 'sbp' ? t('payment.sbpHint') : t('payment.cardHint')}
        </p>

        <span className="rounded-pill bg-ink/5 px-3 py-1 text-xs text-ink-muted">{t('payment.demoNote')}</span>

        <button type="button" onClick={onFail} className="text-sm text-ink-muted underline hover:text-danger">
          {t('payment.simulateFail')}
        </button>
      </div>
    </Modal>
  )
}

function Spinner() {
  return (
    <span
      aria-hidden
      className="h-12 w-12 animate-spin rounded-full border-2 border-line border-t-ink"
    />
  )
}

/** Декоративный QR-плейсхолдер (не настоящий код) для сценария СБП. */
function QrPlaceholder() {
  return (
    <span className="flex h-32 w-32 items-center justify-center rounded-card border border-line bg-surface p-3">
      <svg viewBox="0 0 100 100" className="h-full w-full" aria-hidden fill="var(--color-ink)">
        <rect x="8" y="8" width="24" height="24" rx="4" fill="none" stroke="var(--color-ink)" strokeWidth="6" />
        <rect x="68" y="8" width="24" height="24" rx="4" fill="none" stroke="var(--color-ink)" strokeWidth="6" />
        <rect x="8" y="68" width="24" height="24" rx="4" fill="none" stroke="var(--color-ink)" strokeWidth="6" />
        <rect x="44" y="10" width="6" height="6" />
        <rect x="52" y="18" width="6" height="6" />
        <rect x="44" y="26" width="6" height="6" />
        <rect x="60" y="44" width="6" height="6" />
        <rect x="44" y="52" width="6" height="6" />
        <rect x="70" y="60" width="6" height="6" />
        <rect x="84" y="52" width="6" height="6" />
        <rect x="52" y="70" width="6" height="6" />
        <rect x="68" y="80" width="6" height="6" />
        <rect x="84" y="84" width="6" height="6" />
        <rect x="18" y="44" width="6" height="6" />
        <rect x="10" y="52" width="6" height="6" />
      </svg>
    </span>
  )
}
