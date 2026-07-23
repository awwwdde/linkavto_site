import { useParams } from 'react-router'
import { useQuery } from '@tanstack/react-query'
import { fetchStaticPage } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, ErrorState, PageMeta, Skeleton } from '@/shared/ui'

/** §4: статичные страницы — контент из API `/pages/:slug`. */
const KNOWN_SLUGS = new Set([
  'about',
  'help',
  'privacy',
  'terms',
  'personal-data',
  'public-offer',
  'return-policy',
  'buyer-rules',
  'seller-rules',
])

export function Component() {
  const { slug = '' } = useParams()
  const known = KNOWN_SLUGS.has(slug)

  const page = useQuery({
    queryKey: queryKeys.page(slug),
    queryFn: () => fetchStaticPage(slug),
    enabled: known,
  })

  if (!known) {
    return (
      <Container className="py-12">
        <PageMeta title="Страница не найдена — LINKAVTO" canonicalPath={`/${slug}`} noIndex />
        <EmptyState
          title={t('notFound.title')}
          text={t('notFound.text')}
          action={<ButtonLink to="/">{t('common.toHome')}</ButtonLink>}
        />
      </Container>
    )
  }

  if (page.isPending) {
    return (
      <Container className="flex flex-col gap-4 py-8">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </Container>
    )
  }

  if (page.isError) {
    return (
      <Container className="py-12">
        <ErrorState onRetry={() => void page.refetch()} />
      </Container>
    )
  }

  return (
    <>
      <PageMeta title={`${page.data.title} — LINKAVTO`} canonicalPath={`/${slug}`} />
      <Container className="py-6 lg:py-10">
        <article className="mx-auto flex max-w-[70ch] flex-col gap-4 rounded-card bg-surface p-4 shadow-float lg:p-8">
          <h1 className="text-xl font-semibold lg:text-2xl">{page.data.title}</h1>
          <div
            className="flex flex-col gap-3 text-base leading-relaxed text-ink-muted [&_a]:underline [&_li]:ml-4 [&_li]:list-disc"
            dangerouslySetInnerHTML={{ __html: page.data.html }}
          />
        </article>
      </Container>
    </>
  )
}
