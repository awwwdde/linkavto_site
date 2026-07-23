import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { SITE_ORIGIN } from '@/shared/config'

export function Container({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('mx-auto w-full max-w-page px-4 lg:px-8', className)}>{children}</div>
}

export function Section({
  title,
  action,
  children,
  className,
  headingLevel = 'h2',
}: {
  title?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  headingLevel?: 'h2' | 'h3'
}) {
  const Heading = headingLevel
  return (
    <section className={cn('flex flex-col gap-4', className)}>
      {title ? (
        <div className="flex items-baseline justify-between gap-4">
          <Heading className="text-lg font-semibold lg:text-xl">{title}</Heading>
          {action}
        </div>
      ) : null}
      {children}
    </section>
  )
}

export interface PageMetaProps {
  title: string
  description?: string
  /** Путь без домена, например `/product/kolodki`. Канонический URL — на себя (§14). */
  canonicalPath: string
  ogImage?: string | null
  ogType?: 'website' | 'product' | 'article'
  noIndex?: boolean
}

/**
 * §2: React 19 сам поднимает title/meta/link в <head> — helmet не нужен.
 */
export function PageMeta({
  title,
  description,
  canonicalPath,
  ogImage,
  ogType = 'website',
  noIndex = false,
}: PageMetaProps) {
  const url = `${SITE_ORIGIN}${canonicalPath}`
  return (
    <>
      <title>{title}</title>
      {description ? <meta name="description" content={description} /> : null}
      <link rel="canonical" href={url} />
      {noIndex ? <meta name="robots" content="noindex, follow" /> : null}
      <meta property="og:type" content={ogType} />
      <meta property="og:title" content={title} />
      {description ? <meta property="og:description" content={description} /> : null}
      <meta property="og:url" content={url} />
      {ogImage ? <meta property="og:image" content={ogImage} /> : null}
    </>
  )
}
