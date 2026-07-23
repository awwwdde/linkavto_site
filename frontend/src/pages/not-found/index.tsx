import { t } from '@/shared/i18n'
import { ButtonLink, Container, EmptyState, PageMeta } from '@/shared/ui'
import { SmartSearch } from '@/features/search/SmartSearch'

export function Component() {
  return (
    <>
      <PageMeta title="Страница не найдена — LINKAVTO" canonicalPath="/404" noIndex />

      <Container className="flex flex-col items-center gap-6 py-12">
        <EmptyState
          title={t('notFound.title')}
          text={t('notFound.text')}
          action={<ButtonLink to="/">{t('common.toCatalog')}</ButtonLink>}
          className="w-full"
        />
        <div className="w-full max-w-[640px]">
          <SmartSearch showGarageChip={false} />
        </div>
      </Container>
    </>
  )
}
