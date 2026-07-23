import { Link } from 'react-router'
import { t } from '@/shared/i18n'
import { Container } from '@/shared/ui/Layout'

const COLUMNS: { title: string; links: { to: string; label: string }[] }[] = [
  {
    title: t('footer.buyers'),
    links: [
      { to: '/help', label: t('nav.help') },
      { to: '/return-policy', label: 'Условия возврата' },
      { to: '/buyer-rules', label: 'Правила для покупателей' },
      { to: '/favorites', label: t('nav.favorites') },
    ],
  },
  {
    title: t('footer.sellers'),
    links: [
      { to: '/become-seller', label: t('nav.becomeSeller') },
      { to: '/seller-rules', label: 'Правила для продавцов' },
      { to: '/public-offer', label: 'Публичная оферта' },
    ],
  },
  {
    title: t('footer.company'),
    links: [
      { to: '/about', label: t('nav.about') },
      { to: '/terms', label: 'Пользовательское соглашение' },
      { to: '/privacy', label: 'Политика конфиденциальности' },
      { to: '/personal-data', label: 'Обработка персональных данных' },
    ],
  },
]

export function Footer() {
  return (
    <footer className="mt-12 border-t border-line bg-surface pb-24 lg:pb-12">
      <Container className="flex flex-col gap-8 py-8">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex flex-col gap-2">
            <span className="font-display text-md">LINKAVTO</span>
            <p className="text-sm text-ink-muted">{t('brand.tagline')}</p>
          </div>

          {COLUMNS.map((column) => (
            <nav key={column.title} className="flex flex-col gap-2" aria-label={column.title}>
              <h2 className="text-base font-semibold">{column.title}</h2>
              {column.links.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="flex min-h-10 items-center text-base text-ink-muted transition-colors duration-[--duration-fast] hover:text-ink"
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          ))}
        </div>

        <p className="text-sm text-ink-muted">
          © {new Date().getFullYear()} LINKAVTO. {t('footer.rights')}
        </p>
      </Container>
    </footer>
  )
}
