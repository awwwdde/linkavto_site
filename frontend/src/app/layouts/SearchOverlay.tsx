import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'motion/react'
import { t } from '@/shared/i18n'
import { IconClose } from '@/shared/ui/Icon'
import { SmartSearch } from '@/features/search/SmartSearch'
import { GarageChip } from '@/features/garage/GarageChip'
import { useUiStore } from '@/app/ui-store'

/** §4: на mobile поиск — отдельный полноэкранный оверлей по тапу на строку. */
export function SearchOverlay() {
  const open = useUiStore((state) => state.searchOverlayOpen)
  const close = useUiStore((state) => state.closeSearchOverlay)

  return createPortal(
    <AnimatePresence initial={false}>
      {open ? (
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label={t('search.placeholder')}
          data-lenis-prevent
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ type: 'spring', duration: 0.3, bounce: 0 }}
          className="fixed inset-0 z-50 flex flex-col gap-4 bg-paper p-4"
        >
          <div className="flex items-center gap-2">
            <div className="min-w-0 flex-1">
              <SmartSearch variant="overlay" autoFocus showGarageChip={false} onNavigate={close} />
            </div>
            <button
              type="button"
              onClick={close}
              aria-label={t('nav.close')}
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-pill text-ink-muted"
            >
              <IconClose />
            </button>
          </div>
          <GarageChip className="self-start" />
        </motion.div>
      ) : null}
    </AnimatePresence>,
    document.body,
  )
}
