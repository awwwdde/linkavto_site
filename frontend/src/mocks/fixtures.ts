import type {
  AttributeFacet,
  Banner,
  CategoryNode,
  GarageVehicle,
  HomeSection,
  ImageSet,
  Offer,
  ProductDetail,
  ProductListItem,
  Review,
  SellerBrief,
  ShowIn,
  StaticPage,
  VehicleKind,
  VehicleType,
} from '@/shared/api/types'
import { VEHICLE_INDEX } from './vehicles'

/** Детерминированный псевдослучайный генератор — фикстуры не «прыгают» между перезагрузками. */
function rng(seed: number) {
  let state = seed
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296
    return state / 4294967296
  }
}

function placeholder(label: string, tint: string): ImageSet {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
    <rect width="400" height="400" fill="#FFFFFF"/>
    <circle cx="200" cy="185" r="96" fill="${tint}" opacity="0.12"/>
    <rect x="150" y="150" width="100" height="70" rx="12" fill="${tint}" opacity="0.45"/>
    <text x="200" y="320" font-family="monospace" font-size="26" text-anchor="middle" fill="#5C6670">${label}</text>
  </svg>`
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
  return { thumb: url, card: url, full: url, alt: label }
}

const TYPE_TINTS: Record<VehicleType, string> = {
  car: '#2757FF',
  truck: '#B36000',
  moto: '#A21622',
  special: '#8A6D00',
  tires: '#0E8C7F',
  service: '#6C3FC4',
}

/* ------------------------------------------------------------------ */
/* Дерево категорий до 5 уровней                                       */
/* ------------------------------------------------------------------ */

interface Seed {
  name: string
  children?: Seed[]
}

interface RootSeed extends Seed {
  vehicleType: VehicleType
  showIn: ShowIn
  children: Seed[]
}

/** Ветка на 5 уровней: Двигатель → Система питания → Топливная аппаратура → Насосы. */
const ENGINE_BRANCH: Seed = {
  name: 'Двигатель',
  children: [
    {
      name: 'Система питания',
      children: [
        {
          name: 'Топливная аппаратура',
          children: [{ name: 'Топливные насосы' }, { name: 'Форсунки' }, { name: 'Рампы и регуляторы' }],
        },
        { name: 'Топливные фильтры', children: [{ name: 'Фильтры тонкой очистки' }, { name: 'Фильтры грубой очистки' }] },
      ],
    },
    {
      name: 'Газораспределительный механизм',
      children: [
        { name: 'Ремни и цепи', children: [{ name: 'Ремни ГРМ' }, { name: 'Цепи ГРМ' }] },
        { name: 'Ролики и натяжители' },
      ],
    },
    {
      name: 'Система охлаждения',
      children: [{ name: 'Радиаторы' }, { name: 'Помпы' }, { name: 'Термостаты' }],
    },
    { name: 'Прокладки и сальники' },
  ],
}

const BRAKE_BRANCH: Seed = {
  name: 'Тормозная система',
  children: [
    {
      name: 'Дисковые тормоза',
      children: [
        { name: 'Тормозные диски', children: [{ name: 'Вентилируемые' }, { name: 'Невентилируемые' }] },
        { name: 'Тормозные колодки' },
        { name: 'Суппорты' },
      ],
    },
    { name: 'Барабанные тормоза', children: [{ name: 'Барабаны' }, { name: 'Колодки барабанные' }] },
    { name: 'Гидравлика', children: [{ name: 'Главные цилиндры' }, { name: 'Шланги тормозные' }] },
  ],
}

const SUSPENSION_BRANCH: Seed = {
  name: 'Подвеска',
  children: [
    {
      name: 'Передняя подвеска',
      children: [
        { name: 'Амортизаторы', children: [{ name: 'Газомасляные' }, { name: 'Масляные' }] },
        { name: 'Рычаги и шаровые' },
        { name: 'Стойки стабилизатора' },
      ],
    },
    { name: 'Задняя подвеска', children: [{ name: 'Амортизаторы задние' }, { name: 'Пружины' }] },
    { name: 'Ступицы и подшипники' },
  ],
}

const ROOT_SEEDS: RootSeed[] = [
  {
    name: 'Легковые',
    vehicleType: 'car',
    showIn: 'cars',
    children: [
      ENGINE_BRANCH,
      BRAKE_BRANCH,
      SUSPENSION_BRANCH,
      { name: 'Электрика', children: [{ name: 'Стартеры и генераторы' }, { name: 'Датчики' }, { name: 'Свечи' }] },
      { name: 'Кузов', children: [{ name: 'Бамперы' }, { name: 'Оптика' }, { name: 'Зеркала' }] },
      { name: 'Трансмиссия', children: [{ name: 'Сцепление' }, { name: 'ШРУСы' }] },
    ],
  },
  {
    name: 'Грузовые',
    vehicleType: 'truck',
    showIn: 'trucks',
    children: [
      { name: 'Двигатель грузовой', children: [{ name: 'Топливная система' }, { name: 'Охлаждение' }] },
      { name: 'Пневмосистема', children: [{ name: 'Краны и клапаны' }, { name: 'Ресиверы' }] },
      { name: 'Трансмиссия грузовая', children: [{ name: 'Сцепление' }, { name: 'КПП' }] },
      { name: 'Кабина', children: [{ name: 'Стёкла' }, { name: 'Сиденья' }] },
    ],
  },
  {
    name: 'Мото',
    vehicleType: 'moto',
    showIn: 'moto',
    children: [
      { name: 'Двигатель мото', children: [{ name: 'Поршневая' }, { name: 'Сцепление' }] },
      { name: 'Тормоза мото', children: [{ name: 'Колодки' }, { name: 'Диски' }] },
      { name: 'Экипировка', children: [{ name: 'Шлемы' }, { name: 'Перчатки' }] },
    ],
  },
  {
    name: 'Спецтехника',
    vehicleType: 'special',
    showIn: 'special',
    children: [
      { name: 'Гидравлика', children: [{ name: 'Гидроцилиндры' }, { name: 'Гидронасосы' }] },
      { name: 'Ходовая часть', children: [{ name: 'Гусеницы' }, { name: 'Катки' }] },
      { name: 'Рабочие органы', children: [{ name: 'Ковши' }, { name: 'Зубья' }] },
    ],
  },
  {
    name: 'Шины и диски',
    vehicleType: 'tires',
    showIn: 'tires',
    children: [
      { name: 'Шины', children: [{ name: 'Летние' }, { name: 'Зимние' }, { name: 'Всесезонные' }] },
      { name: 'Диски', children: [{ name: 'Литые' }, { name: 'Штампованные' }, { name: 'Кованые' }] },
    ],
  },
  {
    name: 'Для ТО',
    vehicleType: 'service',
    showIn: 'dlya-to',
    children: [
      { name: 'Масла', children: [{ name: 'Моторные' }, { name: 'Трансмиссионные' }] },
      { name: 'Фильтры', children: [{ name: 'Масляные' }, { name: 'Воздушные' }, { name: 'Салонные' }] },
      { name: 'Жидкости', children: [{ name: 'Тормозные' }, { name: 'Охлаждающие' }] },
    ],
  },
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

let categoryId = 1
/** Слаг глобально уникален — как в Django (суффикс -N при коллизии). */
const usedSlugs = new Map<string, number>()

function uniqueSlug(name: string): string {
  const base = slugify(name)
  const seen = usedSlugs.get(base)
  if (seen === undefined) {
    usedSlugs.set(base, 0)
    return base
  }
  const next = seen + 1
  usedSlugs.set(base, next)
  return `${base}-${next}`
}

function buildNode(
  seed: Seed,
  level: number,
  parentPath: string,
  vehicleType: VehicleType,
  showIn: ShowIn,
): CategoryNode {
  const slug = uniqueSlug(seed.name)
  const path = parentPath ? `${parentPath}/${slug}` : slug
  const children =
    level < 5 ? (seed.children ?? []).map((child) => buildNode(child, level + 1, path, vehicleType, showIn)) : []

  return {
    id: categoryId++,
    name: seed.name,
    slug,
    path,
    level,
    products_count: 0,
    vehicle_type: vehicleType,
    show_in: showIn,
    icon: null,
    has_children: children.length > 0,
    children,
  }
}

export const categoryTree: CategoryNode[] = ROOT_SEEDS.map((seed) =>
  buildNode(seed, 1, '', seed.vehicleType, seed.showIn),
)

export function flatten(nodes: CategoryNode[]): CategoryNode[] {
  return nodes.flatMap((node) => [node, ...flatten(node.children)])
}

const allCategories = flatten(categoryTree)
/** Товары висят на листьях — как и в реальном каталоге. */
const leafCategories = allCategories.filter((node) => node.children.length === 0)

/* ------------------------------------------------------------------ */
/* Товары                                                              */
/* ------------------------------------------------------------------ */

export const sellers: SellerBrief[] = [
  { id: 1, name: 'АвтоЛидер', slug: 'avtolider', rating: 4.8, reviews_count: 412 },
  { id: 2, name: 'ДеталиПро', slug: 'detalipro', rating: 4.5, reviews_count: 176 },
  { id: 3, name: 'ГрузСервис', slug: 'gruzservis', rating: 4.2, reviews_count: 58 },
  { id: 4, name: 'Мото-Склад', slug: 'moto-sklad', rating: 4.9, reviews_count: 233 },
]

const MANUFACTURERS = ['Bosch', 'Febi', 'Sachs', 'TRW', 'Mann-Filter', 'Lemförder', 'NGK', 'Brembo']
const PRODUCT_BRANDS = ['LINKAVTO Original', 'AutoLine', 'PartMax', 'ProDrive']

/** Разброс цен привязан к типу детали, иначе фикстуры выглядят абсурдно. */
const PRICE_BANDS: { match: RegExp; min: number; max: number }[] = [
  { match: /свеч/i, min: 250, max: 1800 },
  { match: /фильтр/i, min: 350, max: 2600 },
  { match: /колодк/i, min: 1200, max: 7500 },
  { match: /диск/i, min: 1800, max: 12000 },
  { match: /амортизатор|стойк/i, min: 2200, max: 14000 },
  { match: /ремень|цеп|ролик/i, min: 700, max: 6500 },
  { match: /насос|помп|термостат/i, min: 1500, max: 11000 },
  { match: /радиатор/i, min: 4000, max: 26000 },
  { match: /сцеплен|кпп|гидроцилиндр|гидронасос/i, min: 6000, max: 60000 },
  { match: /шлем|перчатк/i, min: 2500, max: 30000 },
  { match: /масл|жидкост/i, min: 400, max: 6000 },
]

function priceFor(name: string, random: () => number): number {
  const band = PRICE_BANDS.find((item) => item.match.test(name)) ?? { min: 600, max: 9000 }
  return Math.round((band.min + random() * (band.max - band.min)) / 10) * 10 * 100
}

export interface ProductVehicleLink {
  kind: VehicleKind | 'universal'
  classSlugs: string[]
  brandSlug: string | null
  modelSlug: string | null
  generationSlug: string | null
  modificationSlugs: string[]
}

export const products: ProductDetail[] = []
/** Привязка товара к технике — по ней работают фильтры каскада. */
export const productVehicle = new Map<number, ProductVehicleLink>()

const KIND_BY_VEHICLE_TYPE: Record<VehicleType, VehicleKind | 'universal'> = {
  car: 'car',
  truck: 'truck',
  moto: 'moto',
  special: 'special',
  tires: 'universal',
  service: 'universal',
}

{
  const random = rng(20260723)
  let id = 1

  for (const leaf of leafCategories) {
    const rootType = leaf.vehicle_type ?? 'car'
    const kind = KIND_BY_VEHICLE_TYPE[rootType]
    const count = 10 + Math.floor(random() * 12)

    for (let index = 0; index < count; index += 1) {
      const manufacturer = MANUFACTURERS[Math.floor(random() * MANUFACTURERS.length)]!
      const productBrand = PRODUCT_BRANDS[Math.floor(random() * PRODUCT_BRANDS.length)]!
      const sku = `${manufacturer.slice(0, 2).toUpperCase()}${100000 + Math.floor(random() * 899999)}`
      const name = `${leaf.name} ${manufacturer}`
      const price = priceFor(leaf.name, random)
      const hasDiscount = random() > 0.72
      const oldPrice = hasDiscount ? Math.round(price * (1.15 + random() * 0.35)) : null
      const reviewsCount = random() > 0.45 ? Math.floor(random() * 120) : 0
      const image = placeholder(sku, TYPE_TINTS[rootType])
      const slug = `${leaf.slug}-${sku.toLowerCase()}`

      // Привязка к технике: универсальные детали (шины, ТО) не привязаны к марке.
      let link: ProductVehicleLink = {
        kind,
        classSlugs: [],
        brandSlug: null,
        modelSlug: null,
        generationSlug: null,
        modificationSlugs: [],
      }

      if (kind !== 'universal') {
        const candidates = VEHICLE_INDEX.filter((record) => record.kind === kind)
        const record = candidates[Math.floor(random() * candidates.length)]
        if (record) {
          const model = record.models[Math.floor(random() * record.models.length)]
          const generation = model?.generations[Math.floor(random() * (model.generations.length || 1))]
          link = {
            kind,
            classSlugs: record.classSlugs,
            brandSlug: record.brand.slug,
            modelSlug: model?.slug ?? null,
            generationSlug: generation?.slug ?? null,
            modificationSlugs: (generation?.modifications ?? []).slice(0, 1 + Math.floor(random() * 2)).map((m) => m.slug),
          }
        }
      }

      const breadcrumbs = allCategories
        .filter((node) => leaf.path === node.path || leaf.path.startsWith(`${node.path}/`))
        .sort((a, b) => a.level - b.level)
        .map((node) => ({
          id: node.id,
          name: node.name,
          slug: node.slug,
          path: node.path,
          level: node.level,
          products_count: node.products_count,
        }))

      products.push({
        id,
        name,
        slug,
        sku,
        price,
        old_price: oldPrice,
        discount_percent: oldPrice ? Math.round((1 - price / oldPrice) * 100) : null,
        image,
        images: [image, placeholder(`${sku}-2`, TYPE_TINTS[rootType])],
        rating: reviewsCount > 0 ? Math.round((3.4 + random() * 1.6) * 10) / 10 : null,
        reviews_count: reviewsCount,
        in_stock: random() > 0.12,
        offers_count: 1 + Math.floor(random() * 4),
        manufacturer,
        fits_vehicle: null,
        description_html: `<p>${name}. Соответствует требованиям производителя, устанавливается без доработок.</p><ul><li>Гарантия 12 месяцев</li><li>Сертификат соответствия</li></ul>`,
        description_plain: `${name}. Гарантия 12 месяцев, сертификат соответствия.`,
        oem_number: `${Math.floor(random() * 9) + 1}${Math.floor(random() * 100000)
          .toString()
          .padStart(5, '0')}-${Math.floor(random() * 9000 + 1000)}`,
        crosses: Array.from({ length: 2 + Math.floor(random() * 3) }, () => {
          const crossManufacturer = MANUFACTURERS[Math.floor(random() * MANUFACTURERS.length)]!
          return {
            sku: `${crossManufacturer.slice(0, 2).toUpperCase()}${100000 + Math.floor(random() * 899999)}`,
            manufacturer: crossManufacturer,
            product_slug: null,
          }
        }),
        compatibility: link.brandSlug
          ? VEHICLE_INDEX.filter((record) => record.brand.slug === link.brandSlug)
              .flatMap((record) => record.models.map((model) => `${record.brand.name} ${model.name}`))
              .slice(0, 3)
          : ['Универсальная деталь'],
        attributes: [
          { name: 'Производитель', value: manufacturer },
          { name: 'Бренд товара', value: productBrand },
          { name: 'Вес, кг', value: (0.4 + random() * 6).toFixed(2) },
          { name: 'Тип товара', value: (['Оригинал', 'Аналог', 'Восстановленный'] as const)[id % 3]! },
          { name: 'Сторона установки', value: (['Левая', 'Правая', 'Не применимо'] as const)[id % 3]! },
          { name: 'Гарантия', value: (['6 месяцев', '12 месяцев', '24 месяца'] as const)[id % 3]! },
          {
            name: 'Страна производства',
            value: (['Германия', 'Япония', 'Китай', 'Россия', 'Корея'] as const)[id % 5]!,
          },
        ],
        category: {
          id: leaf.id,
          name: leaf.name,
          slug: leaf.slug,
          path: leaf.path,
          level: leaf.level,
          products_count: 0,
        },
        breadcrumbs,
      })

      productVehicle.set(id, link)
      id += 1
    }
  }

  // Счётчики: каждый узел знает, сколько товаров лежит в его поддереве.
  const countFor = (node: CategoryNode): number => {
    const own = products.filter((product) => product.category.id === node.id).length
    const nested = node.children.reduce((sum, child) => sum + countFor(child), 0)
    node.products_count = own + nested
    return node.products_count
  }
  categoryTree.forEach(countFor)
}

/** Бренд товара берём из атрибутов — отдельного поля в типе списка нет. */
export function productBrandOf(product: ProductDetail): string {
  return product.attributes.find((attribute) => attribute.name === 'Бренд товара')?.value ?? PRODUCT_BRANDS[0]!
}

/**
 * Динамические атрибутные фильтры категории (§5): имя атрибута → GET-параметр.
 * TODO(api): согласовать имена параметров с бэком (сейчас у него `viscosity`,
 * `volume`, `material` и т.п. по категориям — см. API_REQUESTS.md).
 */
export const ATTRIBUTE_FACET_DEFS: { name: string; code: string }[] = [
  { name: 'Тип товара', code: 'attr_grade' },
  { name: 'Сторона установки', code: 'attr_side' },
  { name: 'Гарантия', code: 'attr_warranty' },
  { name: 'Страна производства', code: 'attr_country' },
]

/** Собирает атрибутные фасеты по товарам текущей выборки (пустые группы отбрасывает). */
export function attributeFacetsFrom(items: ProductDetail[]): AttributeFacet[] {
  return ATTRIBUTE_FACET_DEFS.map(({ name, code }) => {
    const counts = new Map<string, number>()
    for (const item of items) {
      const value = item.attributes.find((attribute) => attribute.name === name)?.value
      if (!value) continue
      counts.set(value, (counts.get(value) ?? 0) + 1)
    }
    return {
      code,
      label: name,
      options: [...counts.entries()]
        .map(([value, count]) => ({ value, label: value, count }))
        .sort((a, b) => b.count - a.count),
    }
  }).filter((facet) => facet.options.length > 1)
}

export function toListItem(product: ProductDetail): ProductListItem {
  const {
    id, name, slug, sku, price, old_price, discount_percent, image, rating,
    reviews_count, in_stock, offers_count, manufacturer, fits_vehicle,
  } = product
  return {
    id, name, slug, sku, price, old_price, discount_percent, image, rating,
    reviews_count, in_stock, offers_count, manufacturer, fits_vehicle,
  }
}

export function offersFor(product: ProductDetail): Offer[] {
  const random = rng(product.id * 7919)
  return Array.from({ length: product.offers_count }, (_, index) => {
    const seller = sellers[Math.floor(random() * sellers.length)]!
    return {
      id: product.id * 10 + index,
      seller,
      manufacturer: index === 0 ? product.manufacturer! : MANUFACTURERS[Math.floor(random() * MANUFACTURERS.length)]!,
      price: Math.round(product.price * (0.92 + random() * 0.3)),
      delivery_days: Math.floor(random() * 9),
      stock: 1 + Math.floor(random() * 20),
      is_original: random() > 0.6,
    }
  }).sort((a, b) => a.price - b.price)
}

export function reviewsFor(product: ProductDetail): Review[] {
  if (product.reviews_count === 0) return []
  const random = rng(product.id * 104729)
  const texts = [
    'Встали идеально, скрипов нет. Отходили 15 тысяч — как новые.',
    'Пришло быстро, упаковка целая. Артикул совпал с оригиналом.',
    'Качество среднее, но за эти деньги претензий нет.',
    'Продавец подсказал по совместимости, деталь подошла с первого раза.',
  ]
  return Array.from({ length: Math.min(4, product.reviews_count) }, (_, index) => ({
    id: product.id * 100 + index,
    author: ['Игорь', 'Марина', 'Сергей', 'Алексей'][index] ?? 'Покупатель',
    rating: 3 + Math.floor(random() * 3),
    text: texts[index] ?? texts[0]!,
    created_at: new Date(2026, 2 + index, 5 + index).toISOString(),
  }))
}

export const banners: Banner[] = [
  {
    id: 1,
    title: 'Качественные автозапчасти',
    subtitle: 'Для любых авто и любых задач',
    image: {
      thumb: '/banners/hero-1.png',
      card: '/banners/hero-1.png',
      full: '/banners/hero-1.png',
      alt: 'Качественные автозапчасти для любых авто',
    },
    url: '/garage',
  },
]

export function homeSections(): HomeSection[] {
  const carRoot = categoryTree[0]
  return [
    {
      id: 'new',
      title: 'Новинки',
      url: carRoot ? `/category/${carRoot.path}?sort=newest` : null,
      products: products.slice(0, 12).map(toListItem),
    },
    {
      id: 'bestsellers',
      title: 'Лидеры продаж',
      url: carRoot ? `/category/${carRoot.path}?sort=popular` : null,
      products: products
        .filter((product) => product.reviews_count > 40)
        .slice(0, 12)
        .map(toListItem),
    },
  ]
}

export const garageVehicles: GarageVehicle[] = [
  {
    id: 1,
    vehicle_type: 'car',
    make: 'Lada',
    model: 'Vesta',
    modification: '1.6 MT (106 л.с.)',
    year: 2019,
    vin: null,
    title: 'Lada Vesta 1.6 MT, 2019',
  },
]

export const staticPages: Record<string, StaticPage> = Object.fromEntries(
  (
    [
      ['about', 'О компании'],
      ['help', 'Помощь'],
      ['privacy', 'Политика конфиденциальности'],
      ['terms', 'Пользовательское соглашение'],
      ['personal-data', 'Согласие на обработку персональных данных'],
      ['public-offer', 'Публичная оферта'],
      ['return-policy', 'Условия возврата'],
      ['buyer-rules', 'Правила для покупателей'],
      ['seller-rules', 'Правила для продавцов'],
    ] as const
  ).map(([slug, title]) => [
    slug,
    {
      slug,
      title,
      html: `<p>Раздел «${title}». Текст приходит из админки бэкенда и вставляется санитизированным.</p><p>Если у вас остались вопросы, напишите в поддержку — отвечаем в течение рабочего дня.</p>`,
      updated_at: '2026-05-14T10:00:00Z',
    },
  ]),
)
