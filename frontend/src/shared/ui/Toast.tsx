import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'motion/react'
import { create } from 'zustand'
import { cn } from '@/shared/lib/cn'

export interface ToastItem {
  id: number
  text: string
  tone: 'neutral' | 'ok' | 'danger'
}

interface ToastState {
  items: ToastItem[]
  push: (text: string, tone?: ToastItem['tone']) => void
  dismiss: (id: number) => void
}

let nextId = 1

export const useToastStore = create<ToastState>((set) => ({
  items: [],
  push: (text, tone = 'neutral') => set((state) => ({ items: [...state.items, { id: nextId++, text, tone }] })),
  dismiss: (id) => set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
}))

export const toast = {
  show: (text: string) => useToastStore.getState().push(text),
  ok: (text: string) => useToastStore.getState().push(text, 'ok'),
  error: (text: string) => useToastStore.getState().push(text, 'danger'),
}

const TONES: Record<ToastItem['tone'], string> = {
  neutral: 'bg-ink text-white',
  ok: 'bg-ok text-white',
  danger: 'bg-danger text-white',
}

export function ToastViewport() {
  const items = useToastStore((state) => state.items)
  const dismiss = useToastStore((state) => state.dismiss)

  useEffect(() => {
    if (items.length === 0) return
    const timers = items.map((item) => window.setTimeout(() => dismiss(item.id), 3500))
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [items, dismiss])

  return createPortal(
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-24 z-60 flex flex-col items-center gap-2 px-4 lg:bottom-8"
    >
      <AnimatePresence initial={false}>
        {items.map((item) => (
          <motion.output
            key={item.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ type: 'spring', duration: 0.3, bounce: 0 }}
            className={cn('rounded-pill px-4 py-2 text-base shadow-lift', TONES[item.tone])}
          >
            {item.text}
          </motion.output>
        ))}
      </AnimatePresence>
    </div>,
    document.body,
  )
}
