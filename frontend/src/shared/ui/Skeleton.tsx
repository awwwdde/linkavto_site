import { cn } from '@/shared/lib/cn'

/** Скелетон, а не спиннер (§6). Размеры задаются классами по месту. */
export function Skeleton({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cn('block animate-pulse rounded-control bg-line', className)} />
}
