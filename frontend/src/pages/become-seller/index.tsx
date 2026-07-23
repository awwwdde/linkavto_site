import { t } from '@/shared/i18n'
import { Button, Container, PageMeta, Section } from '@/shared/ui'

const STEPS = [
  { title: 'Регистрация', text: 'Заполните данные компании или ИП — проверка занимает один рабочий день.' },
  { title: 'Загрузка прайса', text: 'Прайс подгружается файлом или по API: артикулы, цены, сроки поставки.' },
  { title: 'Первые заказы', text: 'Покупатели видят ваши предложения в карточках деталей и сравнивают по сроку и цене.' },
]

export function Component() {
  return (
    <>
      <PageMeta
        title="Стать продавцом — LINKAVTO"
        description="Продавайте автозапчасти на LINKAVTO: витрина, заказы и аналитика в кабинете продавца."
        canonicalPath="/become-seller"
      />

      <Container className="flex flex-col gap-10 py-8 lg:py-12">
        <section className="flex flex-col items-center gap-4 text-center">
          <h1 className="max-w-[20ch] font-display text-xl lg:text-2xl">Продавайте запчасти на LINKAVTO</h1>
          <p className="max-w-[52ch] text-md text-ink-muted">
            Покупатели ищут детали по VIN и артикулу — ваши предложения показываются прямо в карточке детали.
          </p>
          <Button
            variant="primary"
            size="lg"
            onClick={() => window.open('https://linkavtoseller.ru', '_blank', 'noopener')}
          >
            {t('nav.becomeSeller')}
          </Button>
        </section>

        <Section title="Как это работает">
          <ol className="grid gap-4 md:grid-cols-3">
            {STEPS.map((step, index) => (
              <li key={step.title} className="flex flex-col gap-2 rounded-card bg-surface p-4 shadow-float">
                <span className="font-mono text-sm text-ink-muted">0{index + 1}</span>
                <h3 className="text-md font-semibold">{step.title}</h3>
                <p className="text-base text-ink-muted">{step.text}</p>
              </li>
            ))}
          </ol>
        </Section>
      </Container>
    </>
  )
}
