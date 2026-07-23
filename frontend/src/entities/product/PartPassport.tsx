import { useState } from 'react'
import { Link } from 'react-router'
import type { CrossReference } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { toast } from '@/shared/ui'
import { IconCheck, IconCopy } from '@/shared/ui/Icon'

function CodeStamp({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error('Скопировать не вышло. Выделите код и скопируйте вручную.')
    }
  }

  return (
    <div className="flex items-center justify-between gap-4 rounded-control border border-line px-3 py-2">
      <div className="flex min-w-0 flex-col">
        <span className="text-xs text-ink-muted">{label}</span>
        <span className="truncate font-mono text-md font-medium">{value}</span>
      </div>
      <button
        type="button"
        onClick={() => void copy()}
        aria-label={t('product.copyCode')}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control text-ink-muted transition-colors duration-[--duration-fast] hover:text-ink"
      >
        {copied ? <IconCheck className="text-ok" /> : <IconCopy />}
      </button>
    </div>
  )
}

export interface PartPassportProps {
  sku: string
  oemNumber: string | null
  crosses: CrossReference[]
  compatibility: string[]
}

/** §1: «Паспорт детали» — техпаспортная подача, все коды моноширинным. */
export function PartPassport({ sku, oemNumber, crosses, compatibility }: PartPassportProps) {
  return (
    <section className="flex flex-col gap-4 rounded-card bg-surface p-4 shadow-float lg:p-6">
      <h2 className="text-md font-semibold">{t('product.passport')}</h2>

      <div className="grid gap-2 sm:grid-cols-2">
        <CodeStamp label={t('product.sku')} value={sku} />
        {oemNumber ? <CodeStamp label={t('product.oem')} value={oemNumber} /> : null}
      </div>

      {crosses.length > 0 ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-base font-semibold">{t('product.crosses')}</h3>
          <ul className="flex flex-wrap gap-2">
            {crosses.map((cross) => (
              <li key={`${cross.manufacturer}-${cross.sku}`}>
                {cross.product_slug ? (
                  <Link
                    to={`/product/${cross.product_slug}`}
                    className="inline-flex min-h-10 items-center gap-2 rounded-pill border border-line px-3 text-sm hover:border-ink-muted"
                  >
                    <span className="text-ink-muted">{cross.manufacturer}</span>
                    <span className="font-mono">{cross.sku}</span>
                  </Link>
                ) : (
                  <span className="inline-flex min-h-10 items-center gap-2 rounded-pill border border-line px-3 text-sm">
                    <span className="text-ink-muted">{cross.manufacturer}</span>
                    <span className="font-mono">{cross.sku}</span>
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {compatibility.length > 0 ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-base font-semibold">{t('product.compatibility')}</h3>
          <ul className="flex flex-col gap-1 text-base text-ink-muted">
            {compatibility.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
