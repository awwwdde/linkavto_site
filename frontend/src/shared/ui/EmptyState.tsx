import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { Button } from './Button'

export interface EmptyStateProps {
  title: string
  /** §9: приглашение к действию, а не «Здесь пусто». */
  text: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ title, text, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-3 rounded-card bg-surface px-6 py-12 text-center shadow-float',
        className,
      )}
    >
      <h2 className="text-md font-semibold">{title}</h2>
      <p className="max-w-[42ch] text-base text-ink-muted">{text}</p>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  )
}

/** §6: error-состояние — текст + retry. */
export function ErrorState({
  onRetry,
  title = t('common.errorTitle'),
  text = t('common.errorText'),
  className,
}: {
  onRetry?: () => void
  title?: string
  text?: string
  className?: string
}) {
  return (
    <EmptyState
      title={title}
      text={text}
      className={className}
      action={
        onRetry ? (
          <Button variant="secondary" onClick={onRetry}>
            {t('common.retry')}
          </Button>
        ) : null
      }
    />
  )
}
