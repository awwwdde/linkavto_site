import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { Address } from '@/shared/api/types'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { toast } from '@/shared/ui'
import { IconMore } from '@/shared/ui/Icon'
import { useAddressStore } from './store'

const MENU_WIDTH = 224

/**
 * Меню-троеточие у адреса: «Сделать основным» и «Удалить».
 * Основной адрес пункт «сделать основным» не показывает — он уже основной.
 *
 * Меню рендерится порталом с fixed-координатами: внутри окна со скроллом
 * выпадашка иначе добавляла бы окну высоту и полосу прокрутки.
 */
export function AddressMenu({ address, className }: { address: Address; className?: string }) {
  const remove = useAddressStore((s) => s.remove)
  const setDefault = useAddressStore((s) => s.setDefault)
  const trigger = useRef<HTMLButtonElement>(null)
  const menu = useRef<HTMLDivElement>(null)
  const [at, setAt] = useState<{ top: number; left: number } | null>(null)

  const open = at !== null
  const close = () => setAt(null)

  const toggle = () => {
    if (open) return close()
    const box = trigger.current?.getBoundingClientRect()
    if (!box) return
    // Ниже кнопки, а у нижней кромки экрана — над ней.
    const below = box.bottom + 4
    const height = address.is_default ? 48 : 88
    const flip = below + height > window.innerHeight - 8
    setAt({
      top: flip ? box.top - height - 4 : below,
      left: Math.max(8, Math.min(box.right - MENU_WIDTH, window.innerWidth - MENU_WIDTH - 8)),
    })
  }

  useEffect(() => {
    if (!open) return
    const onDown = (event: PointerEvent) => {
      const target = event.target as Node
      if (!menu.current?.contains(target) && !trigger.current?.contains(target)) close()
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close()
    }
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    // Позиция посчитана один раз — при скролле или ресайзе просто закрываем.
    window.addEventListener('scroll', close, true)
    window.addEventListener('resize', close)
    return () => {
      document.removeEventListener('pointerdown', onDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('scroll', close, true)
      window.removeEventListener('resize', close)
    }
  }, [open])

  const item =
    'flex h-11 w-full items-center px-3 text-left text-base transition-colors duration-[--duration-fast] hover:bg-paper'

  return (
    <>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t('address.actions')}
        onClick={toggle}
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-control text-ink-muted',
          'transition-colors duration-[--duration-fast] hover:bg-paper hover:text-ink',
          className,
        )}
      >
        <IconMore />
      </button>

      {open
        ? createPortal(
            <div
              ref={menu}
              role="menu"
              style={{ top: at.top, left: at.left, width: MENU_WIDTH }}
              className="fixed z-[60] overflow-hidden rounded-control border border-line bg-surface shadow-lift"
            >
              {!address.is_default ? (
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setDefault(address.id)
                    close()
                  }}
                  className={cn(item, 'text-ink')}
                >
                  {t('address.makeDefault')}
                </button>
              ) : null}

              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  remove(address.id)
                  close()
                  toast.ok(t('address.deleted'))
                }}
                className={cn(item, 'text-danger')}
              >
                {t('address.remove')}
              </button>
            </div>,
            document.body,
          )
        : null}
    </>
  )
}
