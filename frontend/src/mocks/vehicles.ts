import type {
  VehicleBrandOption,
  VehicleClassOption,
  VehicleGenerationOption,
  VehicleKind,
  VehicleModelOption,
  VehicleModificationOption,
} from '@/shared/api/types'

/**
 * Справочники техники по образу моделей Django:
 * CarType/CarBrand/CarModel/CarGeneration/CarModification и аналоги.
 * Любой уровень можно запросить без родителя — тогда отдаётся всё.
 */

export const VEHICLE_KIND_LABEL: Record<VehicleKind, string> = {
  car: 'Легковые',
  truck: 'Грузовые',
  moto: 'Мото',
  special: 'Спецтехника',
}

const CLASS_SEEDS: Record<VehicleKind, { id: number; name: string; slug: string }[]> = {
  car: [
    { id: 1, name: 'Седан', slug: 'sedan' },
    { id: 2, name: 'Хэтчбек', slug: 'hatchback' },
    { id: 3, name: 'Универсал', slug: 'universal' },
    { id: 4, name: 'Внедорожник', slug: 'suv' },
    { id: 5, name: 'Минивэн', slug: 'minivan' },
  ],
  truck: [
    { id: 11, name: 'Седельный тягач', slug: 'tyagach' },
    { id: 12, name: 'Самосвал', slug: 'samosval' },
    { id: 13, name: 'Автобус', slug: 'avtobus' },
    { id: 14, name: 'Фургон', slug: 'furgon' },
  ],
  moto: [
    { id: 21, name: 'Мотоцикл', slug: 'motocikl' },
    { id: 22, name: 'Скутер', slug: 'skuter' },
    { id: 23, name: 'Квадроцикл', slug: 'kvadrocikl' },
  ],
  special: [
    { id: 31, name: 'Экскаватор', slug: 'ekskavator' },
    { id: 32, name: 'Погрузчик', slug: 'pogruzchik' },
    { id: 33, name: 'Бульдозер', slug: 'buldozer' },
  ],
}

export const VEHICLE_CLASSES: Record<VehicleKind, VehicleClassOption[]> = Object.fromEntries(
  (Object.keys(CLASS_SEEDS) as VehicleKind[]).map((kind) => [
    kind,
    CLASS_SEEDS[kind].map((item) => ({ ...item, vehicle_type: kind })),
  ]),
) as Record<VehicleKind, VehicleClassOption[]>

interface BrandSeed {
  name: string
  classes: string[]
  models: { name: string; years: [number, number | null]; generations: string[] }[]
}

const BRAND_SEEDS: Record<VehicleKind, BrandSeed[]> = {
  car: [
    {
      name: 'Lada',
      classes: ['sedan', 'universal', 'hatchback'],
      models: [
        { name: 'Vesta', years: [2015, null], generations: ['I (2015—2022)', 'I рестайлинг (2022—н.в.)'] },
        { name: 'Granta', years: [2011, null], generations: ['I (2011—2018)', 'FL (2018—н.в.)'] },
        { name: 'Largus', years: [2012, null], generations: ['I (2012—2021)', 'FL (2021—н.в.)'] },
        { name: 'Niva Travel', years: [2020, null], generations: ['I (2020—н.в.)'] },
      ],
    },
    {
      name: 'Renault',
      classes: ['sedan', 'hatchback', 'suv'],
      models: [
        { name: 'Logan', years: [2004, 2022], generations: ['I (2004—2014)', 'II (2014—2022)'] },
        { name: 'Duster', years: [2010, null], generations: ['I (2010—2021)', 'II (2021—н.в.)'] },
        { name: 'Sandero', years: [2009, 2022], generations: ['I (2009—2014)', 'II (2014—2022)'] },
      ],
    },
    {
      name: 'Kia',
      classes: ['sedan', 'suv', 'hatchback'],
      models: [
        { name: 'Rio', years: [2005, null], generations: ['III (2011—2017)', 'IV (2017—н.в.)'] },
        { name: 'Sportage', years: [2004, null], generations: ['III (2010—2016)', 'IV (2016—2021)'] },
      ],
    },
    {
      name: 'Hyundai',
      classes: ['sedan', 'suv'],
      models: [
        { name: 'Solaris', years: [2010, 2022], generations: ['I (2010—2017)', 'II (2017—2022)'] },
        { name: 'Creta', years: [2016, null], generations: ['I (2016—2021)', 'II (2021—н.в.)'] },
      ],
    },
    {
      name: 'Toyota',
      classes: ['sedan', 'suv', 'universal'],
      models: [
        { name: 'Camry', years: [1982, null], generations: ['XV50 (2011—2017)', 'XV70 (2017—н.в.)'] },
        { name: 'RAV4', years: [1994, null], generations: ['XA40 (2012—2018)', 'XA50 (2018—н.в.)'] },
      ],
    },
    {
      name: 'Volkswagen',
      classes: ['sedan', 'hatchback', 'universal'],
      models: [
        { name: 'Polo', years: [1975, null], generations: ['V (2009—2020)', 'VI (2020—н.в.)'] },
        { name: 'Tiguan', years: [2007, null], generations: ['I (2007—2016)', 'II (2016—н.в.)'] },
      ],
    },
  ],
  truck: [
    {
      name: 'КамАЗ',
      classes: ['samosval', 'tyagach'],
      models: [
        { name: '5490', years: [2013, null], generations: ['I (2013—н.в.)'] },
        { name: '65115', years: [1998, null], generations: ['I (1998—н.в.)'] },
      ],
    },
    {
      name: 'MAN',
      classes: ['tyagach', 'furgon'],
      models: [
        { name: 'TGX', years: [2007, null], generations: ['I (2007—2020)', 'II (2020—н.в.)'] },
        { name: 'TGS', years: [2007, null], generations: ['I (2007—2020)'] },
      ],
    },
    {
      name: 'Volvo',
      classes: ['tyagach'],
      models: [{ name: 'FH', years: [1993, null], generations: ['III (2008—2013)', 'IV (2013—н.в.)'] }],
    },
  ],
  moto: [
    {
      name: 'Honda',
      classes: ['motocikl', 'skuter'],
      models: [
        { name: 'CB 500', years: [2013, null], generations: ['I (2013—н.в.)'] },
        { name: 'Dio', years: [1988, null], generations: ['AF62 (2003—2012)'] },
      ],
    },
    {
      name: 'Yamaha',
      classes: ['motocikl', 'kvadrocikl'],
      models: [{ name: 'MT-07', years: [2014, null], generations: ['I (2014—2020)', 'II (2021—н.в.)'] }],
    },
  ],
  special: [
    {
      name: 'JCB',
      classes: ['ekskavator', 'pogruzchik'],
      models: [{ name: '3CX', years: [1980, null], generations: ['I (1980—н.в.)'] }],
    },
    {
      name: 'Komatsu',
      classes: ['ekskavator', 'buldozer'],
      models: [{ name: 'PC200', years: [1990, null], generations: ['8 (2006—н.в.)'] }],
    },
  ],
}

const MODIFICATION_SEEDS = [
  { name: '1.6 MT (106 л.с.)', engine: '1.6 бензин', power: 106 },
  { name: '1.6 CVT (113 л.с.)', engine: '1.6 бензин', power: 113 },
  { name: '1.8 MT (122 л.с.)', engine: '1.8 бензин', power: 122 },
  { name: '2.0 AT (150 л.с.)', engine: '2.0 бензин', power: 150 },
  { name: '2.0 TDI (143 л.с.)', engine: '2.0 дизель', power: 143 },
]

function slugify(value: string): string {
  const map: Record<string, string> = {
    а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'zh', з: 'z', и: 'i', й: 'y',
    к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f',
    х: 'h', ц: 'c', ч: 'ch', ш: 'sh', щ: 'sch', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu', я: 'ya',
  }
  return value
    .toLowerCase()
    .split('')
    .map((char) => map[char] ?? char)
    .join('')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

export interface VehicleRecord {
  kind: VehicleKind
  classSlugs: string[]
  brand: VehicleBrandOption
  models: (VehicleModelOption & {
    generations: (VehicleGenerationOption & { modifications: VehicleModificationOption[] })[]
  })[]
}

let seq = 1000

export const VEHICLE_INDEX: VehicleRecord[] = (Object.keys(BRAND_SEEDS) as VehicleKind[]).flatMap((kind) =>
  BRAND_SEEDS[kind].map((seed) => {
    const brandSlug = slugify(seed.name)
    return {
      kind,
      classSlugs: seed.classes,
      brand: {
        id: seq++,
        name: seed.name,
        slug: brandSlug,
        vehicle_type: kind,
        models_count: seed.models.length,
        class_slugs: seed.classes,
      },
      models: seed.models.map((model) => {
        const modelSlug = `${brandSlug}-${slugify(model.name)}`
        return {
          id: seq++,
          name: model.name,
          slug: modelSlug,
          vehicle_type: kind,
          brand_slug: brandSlug,
          brand_name: seed.name,
          year_start: model.years[0],
          year_end: model.years[1],
          generations: model.generations.map((generation, generationIndex) => {
            const generationSlug = `${modelSlug}-gen-${generationIndex + 1}`
            return {
              id: seq++,
              name: generation,
              slug: generationSlug,
              vehicle_type: kind,
              brand_slug: brandSlug,
              model_slug: modelSlug,
              model_name: model.name,
              year_start: model.years[0] + generationIndex * 5,
              year_end: model.years[1],
              modifications: MODIFICATION_SEEDS.slice(0, 2 + (generationIndex % 3)).map((modification, index) => ({
                id: seq++,
                name: modification.name,
                slug: `${generationSlug}-mod-${index + 1}`,
                vehicle_type: kind,
                brand_slug: brandSlug,
                model_slug: modelSlug,
                generation_slug: generationSlug,
                generation_name: `${model.name} ${generation}`,
                engine: modification.engine,
                power: modification.power,
              })),
            }
          }),
        }
      }),
    }
  }),
)

const ALL_KINDS = Object.keys(BRAND_SEEDS) as VehicleKind[]

function kindsOf(kind: VehicleKind | null): VehicleKind[] {
  return kind ? [kind] : ALL_KINDS
}

export function classesOf(kind: VehicleKind | null): VehicleClassOption[] {
  return kindsOf(kind).flatMap((item) => VEHICLE_CLASSES[item])
}

export function brandsOf(kind: VehicleKind | null, classSlug: string | null): VehicleBrandOption[] {
  const kinds = new Set(kindsOf(kind))
  return VEHICLE_INDEX.filter(
    (record) => kinds.has(record.kind) && (!classSlug || record.classSlugs.includes(classSlug)),
  ).map((record) => record.brand)
}

export function modelsOf(kind: VehicleKind | null, brandSlug: string | null): VehicleModelOption[] {
  const kinds = new Set(kindsOf(kind))
  return VEHICLE_INDEX.filter((record) => kinds.has(record.kind) && (!brandSlug || record.brand.slug === brandSlug))
    .flatMap((record) => record.models)
    .map(({ generations: _generations, ...model }) => model)
}

export function generationsOf(kind: VehicleKind | null, modelSlug: string | null): VehicleGenerationOption[] {
  const kinds = new Set(kindsOf(kind))
  return VEHICLE_INDEX.filter((record) => kinds.has(record.kind))
    .flatMap((record) => record.models)
    .filter((model) => !modelSlug || model.slug === modelSlug)
    .flatMap((model) => model.generations)
    .map(({ modifications: _modifications, ...generation }) => generation)
}

export function modificationsOf(
  kind: VehicleKind | null,
  generationSlug: string | null,
): VehicleModificationOption[] {
  const kinds = new Set(kindsOf(kind))
  return VEHICLE_INDEX.filter((record) => kinds.has(record.kind))
    .flatMap((record) => record.models)
    .flatMap((model) => model.generations)
    .filter((generation) => !generationSlug || generation.slug === generationSlug)
    .flatMap((generation) => generation.modifications)
}
