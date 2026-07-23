import { SHARE_TARGETS } from '@/shared/config'
import { t } from '@/shared/i18n'
import { toast } from '@/shared/ui'
import { IconCopy, IconShare } from '@/shared/ui/Icon'

/** §10.3: реальные URL текущей страницы, никаких плейсхолдеров. */
export function ShareButtons({ title }: { title: string }) {
  const url = typeof window === 'undefined' ? '' : window.location.href

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      toast.ok(t('product.copied'))
    } catch {
      toast.error('Скопировать не вышло. Скопируйте адрес из адресной строки.')
    }
  }

  return (
    <div className="flex items-center gap-2">
      <span className="flex items-center gap-1 text-sm text-ink-muted">
        <IconShare width={16} height={16} />
        {t('product.share')}
      </span>
      {SHARE_TARGETS.map((target) => (
        <a
          key={target.id}
          href={target.href(url)}
          target="_blank"
          rel="noreferrer noopener"
          aria-label={`${t('product.share')}: ${target.label}`}
          title={`${title} — ${target.label}`}
          className="flex h-10 items-center rounded-control px-3 text-sm text-ink-muted transition-colors duration-[--duration-fast] hover:bg-ink/5 hover:text-ink"
        >
          {target.label}
        </a>
      ))}
      <button
        type="button"
        onClick={() => void copy()}
        aria-label={t('product.copyLink')}
        className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted transition-colors duration-[--duration-fast] hover:bg-ink/5 hover:text-ink"
      >
        <IconCopy width={18} height={18} />
      </button>
    </div>
  )
}
