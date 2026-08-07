import { useCallback, useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'motion/react'
import { cn } from '@/shared/lib/cn'
import { t } from '@/shared/i18n'
import { IconClose } from './Icon'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

function useModalBehaviour(open: boolean, onClose: () => void) {
  const ref = useRef<HTMLDivElement>(null)
  const restoreTo = useRef<HTMLElement | null>(null)

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!open) return
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
        return
      }
      if (event.key !== 'Tab' || !ref.current) return
      const nodes = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (node) => node.offsetParent !== null,
      )
      const first = nodes[0]
      const last = nodes[nodes.length - 1]
      if (!first || !last) return
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    [open, onClose],
  )

  useEffect(() => {
    if (!open) return
    restoreTo.current = document.activeElement as HTMLElement | null
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeyDown)
    const timer = window.setTimeout(() => {
      const target = ref.current?.querySelector<HTMLElement>(FOCUSABLE)
      target?.focus()
    }, 0)
    return () => {
      window.clearTimeout(timer)
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = overflow
      restoreTo.current?.focus()
    }
  }, [open, onKeyDown])

  return ref
}

export interface OverlayProps {
  open: boolean
  onClose: () => void
  title: string
  /** Заголовок скрыт визуально, но доступен скринридеру. */
  hideTitle?: boolean
  children: ReactNode
  className?: string
}

export interface ModalProps extends OverlayProps {
  /**
   * Максимальная ширина окна в пикселях. Задана числом, а не классом, потому
   * что меняется по ходу сценария и анимируется (список → карта).
   */
  maxWidth?: number
}

/** §7: портал, Esc, клик по фону, блокировка скролла, возврат фокуса. */
export function Modal({ open, onClose, title, hideTitle, children, className, maxWidth }: ModalProps) {
  const ref = useModalBehaviour(open, onClose)
  const width = maxWidth ? { maxWidth } : null

  return createPortal(
    <AnimatePresence initial={false}>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-6">
          <motion.div
            className="absolute inset-0 bg-ink/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.div
            ref={ref}
            role="dialog"
            aria-modal="true"
            aria-label={title}
            data-lenis-prevent
            initial={{ opacity: 0, y: 12, ...width }}
            animate={{ opacity: 1, y: 0, ...width }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ type: 'spring', duration: 0.35, bounce: 0 }}
            className={cn(
              'relative w-full overflow-y-auto rounded-t-card bg-surface p-6 shadow-lift',
              !maxWidth && 'max-w-[480px]',
              'max-h-[90dvh] sm:rounded-card',
              className,
            )}
          >
            <div className="mb-4 flex items-start justify-between gap-4">
              <h2 className={cn('text-lg font-semibold', hideTitle && 'sr-only')}>{title}</h2>
              <button
                type="button"
                onClick={onClose}
                aria-label={t('nav.close')}
                className="-mr-2 -mt-2 flex h-10 w-10 items-center justify-center rounded-control text-ink-muted hover:bg-ink/5"
              >
                <IconClose />
              </button>
            </div>
            {children}
          </motion.div>
        </div>
      ) : null}
    </AnimatePresence>,
    document.body,
  )
}

/** Мобильная шторка — тот же контракт поведения, другая геометрия (§8). */
export function BottomSheet({ open, onClose, title, hideTitle, children, className }: OverlayProps) {
  const ref = useModalBehaviour(open, onClose)

  return createPortal(
    <AnimatePresence initial={false}>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-end">
          <motion.div
            className="absolute inset-0 bg-ink/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.div
            ref={ref}
            role="dialog"
            aria-modal="true"
            aria-label={title}
            data-lenis-prevent
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', duration: 0.3, bounce: 0 }}
            className={cn(
              'relative flex max-h-[85dvh] w-full flex-col rounded-t-card bg-surface shadow-lift',
              className,
            )}
          >
            <div className="flex items-center justify-between gap-4 border-b border-line px-4 py-4">
              <h2 className={cn('text-md font-semibold', hideTitle && 'sr-only')}>{title}</h2>
              <button
                type="button"
                onClick={onClose}
                aria-label={t('nav.close')}
                className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted hover:bg-ink/5"
              >
                <IconClose />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">{children}</div>
          </motion.div>
        </div>
      ) : null}
    </AnimatePresence>,
    document.body,
  )
}
