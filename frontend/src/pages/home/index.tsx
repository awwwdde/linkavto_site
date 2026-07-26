import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { CategoryNode, VehicleType } from '@/shared/api/types'
import { fetchCategoryTree } from '@/entities/category/api'
import { CategoryTile } from '@/entities/category/CategoryTile'
import { fetchHomeSections } from '@/shared/api/misc'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { Button, Chip, Container, ErrorState, Modal, PageMeta, Skeleton } from '@/shared/ui'
import {
  IconGarage,
  IconPlus,
  IconTypeCar,
  IconTypeMoto,
  IconTypeService,
  IconTypeSpecial,
  IconTypeTires,
  IconTypeTruck,
  type IconComponent,
} from '@/shared/ui/Icon'
import { PromoCarousel } from '@/app/layouts/PromoCarousel'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { ProductRow } from '@/app/layouts/ProductRow'
import { GarageVehicleForm } from '@/features/garage/GarageVehicleForm'
import { useActiveVehicle } from '@/features/garage/store'

/** vehicle_type → нейтральная lucide-иконка типа техники (§4а). */
const TYPE_ICON: Record<VehicleType, IconComponent> = {
  car: IconTypeCar,
  truck: IconTypeTruck,
  moto: IconTypeMoto,
  special: IconTypeSpecial,
  tires: IconTypeTires,
  service: IconTypeService,
}

function typeIcon(type: VehicleType | null) {
  const Ico = (type && TYPE_ICON[type]) || IconGarage
  return <Ico width={24} height={24} />
}

/** Зона 2 (§4б): выбор техники — бенто плиток. */
function TechBento() {
  const tree = useQuery({ queryKey: queryKeys.categories.tree(), queryFn: fetchCategoryTree })

  if (tree.isPending) {
    return (
      <div className="grid grid-cols-3 gap-3 lg:grid-cols-6 lg:gap-4">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="aspect-square rounded-card" />
        ))}
      </div>
    )
  }

  if (tree.isError) return <ErrorState onRetry={() => void tree.refetch()} />

  return (
    <div className="grid grid-cols-3 gap-3 lg:grid-cols-6 lg:gap-4">
      {(tree.data as CategoryNode[]).map((node) => (
        <CategoryTile
          key={node.id}
          to={`/category/${node.path}`}
          name={node.name}
          icon={typeIcon(node.vehicle_type)}
        />
      ))}
    </div>
  )
}

/** Зона 3 (§4б, §3.4 правило тёмной паузы): полоса гаража. */
function GarageBand() {
  const [formOpen, setFormOpen] = useState(false)
  const active = useActiveVehicle()

  return (
    <section className="flex flex-col gap-5 rounded-card bg-ink p-6 lg:flex-row lg:items-center lg:justify-between lg:p-10">
      <div className="flex flex-col gap-4">
        <SectionHeading dark size="xl" lead={t('home.garageLead')} ghost={t('home.garageGhost')} />
        {active ? (
          <span className="inline-flex w-fit items-center gap-2 rounded-pill border border-white/15 bg-white/10 px-4 py-2 text-base font-medium text-white">
            <IconTypeCar width={16} height={16} />
            {active.title}
          </span>
        ) : null}
      </div>
      <Button variant="primary" size="lg" className="shrink-0" onClick={() => setFormOpen(true)}>
        <IconPlus width={18} height={18} />
        {t('garage.add')}
      </Button>

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={t('garage.add')}>
        <GarageVehicleForm onDone={() => setFormOpen(false)} />
      </Modal>
    </section>
  )
}

const LANE_CHIPS: string[][] = [
  ['Хиты', 'Со скидкой', 'Оригинал', 'До 1000 ₽'],
  ['Новинки недели', 'Топ продаж', 'Аккумуляторы', 'Расходники'],
]

function chipRow(labels: string[]) {
  return labels.map((label) => (
    <Chip key={label} className="shrink-0">
      {label}
    </Chip>
  ))
}

/** Зоны 4+ (§4б): ленты товаров без заголовков. Первая — персональная по гаражу. */
function HomeLanes() {
  const sections = useQuery({ queryKey: queryKeys.home.sections(), queryFn: fetchHomeSections })
  const active = useActiveVehicle()

  if (sections.isPending) {
    return (
      <div className="flex flex-col gap-10">
        {Array.from({ length: 2 }, (_, i) => (
          <div key={i} className="flex flex-col gap-3">
            <Skeleton className="h-8 w-64 rounded-pill" />
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              {Array.from({ length: 5 }, (_, j) => (
                <Skeleton key={j} className="h-64 rounded-card" />
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (sections.isError) return <ErrorState onRetry={() => void sections.refetch()} />

  const lanes = sections.data.filter((section) => section.products.length > 0)

  return (
    <div className="flex flex-col gap-10 lg:gap-14">
      {lanes.map((section, i) => {
        const personalized = i === 0 && active !== null
        return (
          <ProductRow
            key={section.id}
            products={section.products.slice(0, 5)}
            featured={i === 0}
            chips={chipRow(LANE_CHIPS[i % LANE_CHIPS.length] ?? [])}
            label={personalized ? `${t('home.forYour')} ${active.title}` : undefined}
          />
        )
      })}
    </div>
  )
}

export function Component() {
  return (
    <>
      <PageMeta
        title="LINKAVTO — маркетплейс автозапчастей"
        description="Подбор автозапчастей по VIN, артикулу и гаражу. Легковые, грузовые, мото и спецтехника от проверенных продавцов."
        canonicalPath="/"
      />

      {/* Отменяем отступ RootLayout под fixed-шапку — баннер уходит под шапку (§4б зона 1). */}
      <div className="-mt-14 lg:-mt-20">
        <PromoCarousel />

        {/* Шов: контент наезжает на баннер. Нахлёст ≥ радиуса, иначе скруглённые
            углы уходят ниже баннера и открывают зазор. Мобайл — меньшее скругление (§4б). */}
        <div className="relative -mt-6 rounded-t-card bg-paper lg:-mt-40 lg:rounded-t-seam">
          <Container className="flex flex-col gap-10 pt-8 pb-4 lg:gap-14 lg:pt-12">
            {/* Зона 2 */}
            <section className="flex flex-col gap-6">
              <SectionHeading
                size="xl"
                lead={t('home.chooseTechLead')}
                ghost={t('home.chooseTechGhost')}
              />
              <TechBento />
            </section>

            {/* Зона 3 */}
            <GarageBand />

            {/* Зоны 4+ */}
            <HomeLanes />
          </Container>
        </div>
      </div>
    </>
  )
}
