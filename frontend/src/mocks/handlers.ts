import { HttpResponse, http, delay } from 'msw'
import type {
  AuthUser,
  CartItem,
  CategoryBrief,
  CategoryDetail,
  CategoryNode,
  FacetOption,
  Order,
  OrderStatus,
  GarageVehicle,
  PriceHistogramBucket,
  ProductDetail,
  ProductListItem,
  ProductListResponse,
  SearchResponse,
  TireWheelFacets,
  VehicleKind,
  VehicleType,
} from '@/shared/api/types'
import { detectSearchMode } from '@/features/search/detect'
import { CLASS_PARAM } from '@/features/catalog-filters/useCatalogParams'
import {
  ATTRIBUTE_FACET_DEFS,
  attributeFacetsFrom,
  banners,
  categoryTree,
  flatten,
  garageVehicles,
  homeSections,
  offersFor,
  productBrandOf,
  products,
  productVehicle,
  reviewsFor,
  sellers,
  staticPages,
  toListItem,
} from './fixtures'
import { brandsOf, classesOf, generationsOf, modelsOf, modificationsOf } from './vehicles'

const BASE = '/api/v1'

function kindParam(requestUrl: string): VehicleKind | null {
  return (new URL(requestUrl).searchParams.get('vehicle_type') as VehicleKind | null) ?? null
}

const allCategories = flatten(categoryTree)
const bySlug = new Map(allCategories.map((node) => [node.slug, node]))

function brief(node: CategoryNode): CategoryBrief {
  return {
    id: node.id,
    name: node.name,
    slug: node.slug,
    path: node.path,
    level: node.level,
    products_count: node.products_count,
  }
}

function parentOf(node: CategoryNode): CategoryNode | null {
  const parentPath = node.path.split('/').slice(0, -1).join('/')
  if (!parentPath) return null
  return allCategories.find((item) => item.path === parentPath) ?? null
}

function chainTo(node: CategoryNode): CategoryNode[] {
  const chain: CategoryNode[] = []
  let current: CategoryNode | null = node
  while (current) {
    chain.unshift(current)
    current = parentOf(current)
  }
  return chain
}

/** Товары категории — включая все подкатегории на любой глубине. */
function productsOfCategory(slug: string): ProductDetail[] {
  const node = bySlug.get(slug)
  if (!node) return []
  const ids = new Set(flatten([node]).map((item) => item.id))
  return products.filter((product) => ids.has(product.category.id))
}

function histogram(items: ProductDetail[]): PriceHistogramBucket[] {
  if (items.length === 0) return []
  const prices = items.map((item) => item.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const step = Math.max(1, Math.ceil((max - min) / 20))
  return Array.from({ length: 20 }, (_, index) => {
    const from = min + index * step
    const to = from + step
    return { from, to, count: prices.filter((price) => price >= from && price < to).length }
  })
}

function facetsFrom(items: ProductDetail[], pick: (product: ProductDetail) => string | null): FacetOption[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    const value = pick(item)
    if (!value) continue
    counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return [...counts.entries()]
    .map(([value, count]) => ({ value, label: value, count }))
    .sort((a, b) => b.count - a.count)
}

function numericFacet(values: (string | number)[]): FacetOption[] {
  const counts = new Map<string, number>()
  for (const value of values) {
    const key = String(value)
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return [...counts.entries()]
    .map(([value, count]) => ({ value, label: value, count }))
    .sort((a, b) => Number(a.value) - Number(b.value))
}

/** Профильные фасеты отдаём только в шинных категориях (как Category.show_in='tires'). */
function tireWheelFacetsFor(slug: string): TireWheelFacets | null {
  const node = bySlug.get(slug)
  if (!node || node.show_in !== 'tires') return null
  return {
    tire_diameter: numericFacet([13, 14, 15, 16, 17, 18, 19, 20]),
    tire_width: numericFacet([175, 185, 195, 205, 215, 225, 235]),
    tire_height: numericFacet([45, 50, 55, 60, 65, 70]),
    tire_seasonality: [
      { value: 'summer', label: 'Летние', count: 42 },
      { value: 'winter', label: 'Зимние', count: 38 },
      { value: 'all-season', label: 'Всесезонные', count: 12 },
    ],
    wheel_diameter: numericFacet([14, 15, 16, 17, 18, 19]),
    wheel_width: numericFacet([5.5, 6, 6.5, 7, 7.5, 8]),
    wheel_pcd: [
      { value: '4x98', label: '4×98', count: 18 },
      { value: '4x100', label: '4×100', count: 26 },
      { value: '5x108', label: '5×108', count: 21 },
      { value: '5x114.3', label: '5×114.3', count: 33 },
    ],
    wheel_offset_type: [
      { value: 'et35', label: 'ET35', count: 14 },
      { value: 'et40', label: 'ET40', count: 22 },
      { value: 'et45', label: 'ET45', count: 17 },
    ],
    wheel_type: [
      { value: 'alloy', label: 'Литой', count: 40 },
      { value: 'steel', label: 'Штампованный', count: 25 },
      { value: 'forged', label: 'Кованый', count: 9 },
    ],
  }
}

function sortProducts(items: ProductDetail[], sort: string | null): ProductDetail[] {
  const sorted = [...items]
  switch (sort) {
    case 'price_asc':
      return sorted.sort((a, b) => a.price - b.price)
    case 'price_desc':
      return sorted.sort((a, b) => b.price - a.price)
    case 'newest':
      return sorted.sort((a, b) => b.id - a.id)
    case 'popular':
    default:
      return sorted.sort((a, b) => b.reviews_count - a.reviews_count)
  }
}

/** Каскад подбора: те же имена параметров, что и в shop/views.py. */
function applyVehicleFilters(items: ProductDetail[], url: URL): ProductDetail[] {
  const kind = url.searchParams.get('vehicle_type') as VehicleKind | null
  if (!kind) return items

  const classSlug = url.searchParams.get(CLASS_PARAM[kind])
  const brand = url.searchParams.get('brand')
  const model = url.searchParams.get('model')
  const generation = url.searchParams.get('generation')
  const modification = url.searchParams.get('modification')

  return items.filter((product) => {
    const link = productVehicle.get(product.id)
    if (!link) return false
    // Универсальные детали подходят любой технике.
    if (link.kind === 'universal') return true
    if (link.kind !== kind) return false
    if (classSlug && !link.classSlugs.includes(classSlug)) return false
    if (brand && link.brandSlug !== brand) return false
    if (model && link.modelSlug !== model) return false
    if (generation && link.generationSlug !== generation) return false
    if (modification && !link.modificationSlugs.includes(modification)) return false
    return true
  })
}

function listResponse(source: ProductDetail[], url: URL, categorySlug: string | null): ProductListResponse {
  const page = Number(url.searchParams.get('page') ?? 1)
  const pageSize = Number(url.searchParams.get('page_size') ?? 24)
  const vehicleId = url.searchParams.get('garage_vehicle_id')

  let items = applyVehicleFilters(source, url)

  const priceMin = url.searchParams.get('price_min')
  const priceMax = url.searchParams.get('price_max')
  if (priceMin) items = items.filter((item) => item.price >= Number(priceMin))
  if (priceMax) items = items.filter((item) => item.price <= Number(priceMax))

  const manufacturer = url.searchParams.get('manufacturer')
  if (manufacturer) {
    const set = new Set(manufacturer.split(','))
    items = items.filter((item) => item.manufacturer && set.has(item.manufacturer))
  }

  const productBrand = url.searchParams.get('product_brand')
  if (productBrand) {
    const set = new Set(productBrand.split(','))
    items = items.filter((item) => set.has(productBrandOf(item)))
  }

  if (url.searchParams.get('in_stock') === 'true') items = items.filter((item) => item.in_stock)
  if (url.searchParams.get('on_order') === 'true') items = items.filter((item) => !item.in_stock)
  if (url.searchParams.get('is_original') === 'true') items = items.filter((item) => item.id % 3 === 0)

  // Динамические атрибутные фильтры (attr_*), мультивыбор CSV.
  for (const { name, code } of ATTRIBUTE_FACET_DEFS) {
    const raw = url.searchParams.get(code)
    if (!raw) continue
    const set = new Set(raw.split(','))
    items = items.filter((item) => {
      const value = item.attributes.find((attribute) => attribute.name === name)?.value
      return value ? set.has(value) : false
    })
  }

  // Гараж: подставляем совместимость вместо ручного каскада.
  if (vehicleId) items = items.filter((item) => item.id % 4 !== 0)

  const sorted = sortProducts(items, url.searchParams.get('sort'))
  const start = (page - 1) * pageSize
  const results: ProductListItem[] = sorted.slice(start, start + pageSize).map((product) => {
    const item = toListItem(product)
    const matched = vehicleId || url.searchParams.get('vehicle_type')
    return matched ? { ...item, fits_vehicle: true } : item
  })

  const prices = source.map((item) => item.price)

  return {
    count: sorted.length,
    next: page * pageSize < sorted.length ? `?page=${page + 1}` : null,
    previous: page > 1 ? `?page=${page - 1}` : null,
    results,
    price_histogram: histogram(source),
    facets: {
      manufacturers: facetsFrom(source, (product) => product.manufacturer),
      product_brands: facetsFrom(source, productBrandOf),
      price_min: prices.length ? Math.min(...prices) : 0,
      price_max: prices.length ? Math.max(...prices) : 0,
      tire_wheel: categorySlug ? tireWheelFacetsFor(categorySlug) : null,
      attributes: attributeFacetsFrom(source),
    },
  }
}

let vehicleSeq = 100
const vehicles: GarageVehicle[] = [...garageVehicles]

/* --- Покупатели (мок): аккаунт создаётся при первом входе по коду. --- */
let userSeq = 1
const usersByEmail = new Map<string, AuthUser>()
let currentEmail: string | null = null

function getOrCreateUser(email: string): AuthUser {
  const existing = usersByEmail.get(email)
  if (existing) return existing
  const user: AuthUser = {
    id: ++userSeq,
    email,
    first_name: null,
    last_name: null,
    phone: null,
    avatar: null,
    profile_completed: false,
  }
  usersByEmail.set(email, user)
  return user
}

/* --- Заказы (мок): сохраняются per-email в localStorage, чтобы тестовый заказ
   отображался в профиле и пережил перезагрузку. --- */
const ORDERS_KEY = 'linkavto:mock-orders'

function loadOrders(): Record<string, Order[]> {
  try {
    return JSON.parse(localStorage.getItem(ORDERS_KEY) ?? '{}') as Record<string, Order[]>
  } catch {
    return {}
  }
}

function saveOrders(map: Record<string, Order[]>): void {
  try {
    localStorage.setItem(ORDERS_KEY, JSON.stringify(map))
  } catch {
    /* приватный режим — заказ живёт только в этой сессии */
  }
}

let orderSeq = Math.max(
  5000,
  ...Object.values(loadOrders())
    .flat()
    .map((order) => order.id),
)

const STATUS_DISPLAY: Record<OrderStatus, string> = {
  new: 'Новый',
  paid: 'Оплачен',
  shipping: 'В доставке',
  done: 'Выполнен',
  canceled: 'Отменён',
}

interface OrderBody {
  delivery_method: Order['delivery_method']
  payment_method: Order['payment_method']
  items: { product_id: number; offer_id: number | null; quantity: number }[]
  city?: string
  address?: string
}

function buildOrder(body: OrderBody): Order {
  const id = ++orderSeq
  const items: CartItem[] = (body.items ?? []).map((line, index) => {
    const product = products.find((p) => p.id === line.product_id)
    const listItem = product ? toListItem(product) : null
    const price = product?.price ?? 0
    return {
      id: index + 1,
      // Фолбэк на случай, если товар не нашёлся (демо).
      product: listItem ?? ({ id: line.product_id, name: 'Товар', slug: '', sku: '', price, old_price: null, discount_percent: null, image: null, rating: null, reviews_count: 0, in_stock: true, offers_count: 0, manufacturer: null, fits_vehicle: null } as ProductListItem),
      offer: null,
      quantity: line.quantity,
      price,
      total: price * line.quantity,
    }
  })

  const subtotal = items.reduce((sum, item) => sum + item.total, 0)
  const delivery = body.delivery_method === 'pickup' ? 0 : 39000
  const status: OrderStatus = body.payment_method === 'cash' ? 'new' : 'paid'

  return {
    id,
    number: `LA-${id}`,
    status,
    status_display: STATUS_DISPLAY[status],
    created_at: new Date().toISOString(),
    total: subtotal + delivery,
    items,
    delivery_address:
      body.delivery_method === 'pickup' ? 'Самовывоз / пункт выдачи' : [body.city, body.address].filter(Boolean).join(', ') || null,
    delivery_method: body.delivery_method,
    payment_method: body.payment_method,
  }
}

export const handlers = [
  http.get(`${BASE}/categories/tree/`, async () => {
    await delay(120)
    return HttpResponse.json(categoryTree)
  }),

  http.get(`${BASE}/categories/:slug/`, async ({ params }) => {
    await delay(120)
    const node = bySlug.get(String(params['slug']))
    if (!node) return new HttpResponse(null, { status: 404 })

    const parent = parentOf(node)
    const siblings = parent ? parent.children : categoryTree

    const detail: CategoryDetail = {
      ...brief(node),
      vehicle_type: node.vehicle_type,
      show_in: node.show_in,
      description: null,
      breadcrumbs: chainTo(node).map(brief),
      children: node.children.map(brief),
      siblings: siblings.map(brief),
    }
    return HttpResponse.json(detail)
  }),

  /* --- Справочники техники для каскада подбора --- */

  // Родитель необязателен: без него отдаём полный список — шаги подбора
  // не блокируют друг друга.
  http.get(`${BASE}/catalog/vehicle-classes/`, async ({ request }) => {
    await delay(100)
    return HttpResponse.json(classesOf(kindParam(request.url)))
  }),

  http.get(`${BASE}/catalog/brands/`, async ({ request }) => {
    await delay(120)
    const url = new URL(request.url)
    return HttpResponse.json(brandsOf(kindParam(request.url), url.searchParams.get('class')))
  }),

  http.get(`${BASE}/catalog/models/`, async ({ request }) => {
    await delay(120)
    const url = new URL(request.url)
    return HttpResponse.json(modelsOf(kindParam(request.url), url.searchParams.get('brand')))
  }),

  http.get(`${BASE}/catalog/generations/`, async ({ request }) => {
    await delay(120)
    const url = new URL(request.url)
    return HttpResponse.json(generationsOf(kindParam(request.url), url.searchParams.get('model')))
  }),

  http.get(`${BASE}/catalog/modifications/`, async ({ request }) => {
    await delay(120)
    const url = new URL(request.url)
    return HttpResponse.json(modificationsOf(kindParam(request.url), url.searchParams.get('generation')))
  }),

  /* --- Товары --- */

  http.get(`${BASE}/products/`, async ({ request }) => {
    await delay(180)
    const url = new URL(request.url)
    const category = url.searchParams.get('category')
    const seller = url.searchParams.get('seller')
    let source = category ? productsOfCategory(category) : products
    if (seller) source = source.filter((product) => product.id % sellers.length === Number(seller) % sellers.length)
    return HttpResponse.json(listResponse(source, url, category))
  }),

  http.get(`${BASE}/products/:slug/offers/`, async ({ params }) => {
    await delay(200)
    const product = products.find((item) => item.slug === params['slug'])
    if (!product) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(offersFor(product))
  }),

  http.get(`${BASE}/products/:slug/similar/`, async ({ params }) => {
    await delay(220)
    const product = products.find((item) => item.slug === params['slug'])
    if (!product) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(
      products
        .filter((item) => item.category.id === product.category.id && item.id !== product.id)
        .slice(0, 8)
        .map(toListItem),
    )
  }),

  http.get(`${BASE}/products/:slug/reviews/`, async ({ params }) => {
    await delay(200)
    const product = products.find((item) => item.slug === params['slug'])
    if (!product) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(reviewsFor(product))
  }),

  http.post(`${BASE}/products/:slug/reviews/`, async () => {
    await delay(400)
    return HttpResponse.json({ id: 9999, author: 'Вы', rating: 5, text: '', created_at: new Date().toISOString() }, { status: 201 })
  }),

  http.get(`${BASE}/products/:slug/`, async ({ params }) => {
    await delay(150)
    const product = products.find((item) => item.slug === params['slug'])
    if (!product) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(product)
  }),

  /* --- Поиск --- */

  http.get(`${BASE}/search/suggest/`, async ({ request }) => {
    await delay(100)
    const q = (new URL(request.url).searchParams.get('q') ?? '').toLowerCase()
    if (q.length < 2) return HttpResponse.json([])

    const productHits = products
      .filter((item) => item.name.toLowerCase().includes(q) || item.sku.toLowerCase().includes(q))
      .slice(0, 6)
      .map((item) => ({
        type: 'product' as const,
        title: item.name,
        subtitle: item.sku,
        url: `/product/${item.slug}`,
      }))

    const categoryHits = allCategories
      .filter((node) => node.name.toLowerCase().includes(q))
      .slice(0, 3)
      .map((node) => ({
        type: 'category' as const,
        title: node.name,
        subtitle: `${node.products_count} товаров`,
        url: `/category/${node.path}`,
      }))

    return HttpResponse.json([...productHits, ...categoryHits])
  }),

  http.get(`${BASE}/search/`, async ({ request }) => {
    await delay(220)
    const url = new URL(request.url)
    const q = url.searchParams.get('q') ?? ''
    const requested = url.searchParams.get('type') ?? 'auto'
    const mode = requested === 'auto' ? detectSearchMode(q) : (requested as SearchResponse['resolved_mode'])
    const needle = q.trim().toLowerCase()

    let source: ProductDetail[]
    if (mode === 'vin') {
      source = products.filter((item) => item.category.name.toLowerCase().includes('фильтр'))
    } else if (mode === 'sku') {
      source = products.filter(
        (item) =>
          item.sku.toLowerCase().includes(needle) ||
          item.crosses.some((cross) => cross.sku.toLowerCase().includes(needle)),
      )
    } else {
      source = products.filter((item) => item.name.toLowerCase().includes(needle))
    }

    const base = listResponse(source, url, null)
    const response: SearchResponse = {
      count: base.count,
      next: base.next,
      previous: base.previous,
      results: base.results,
      resolved_mode: mode,
      vehicle: mode === 'vin' ? (vehicles[0] ?? null) : null,
      categories: allCategories
        .filter((node) => needle.length > 1 && node.name.toLowerCase().includes(needle))
        .slice(0, 6)
        .map(brief),
    }
    return HttpResponse.json(response)
  }),

  /* --- Авторизация --- */

  http.post(`${BASE}/auth/email-code/`, async () => {
    await delay(400)
    return HttpResponse.json({ detail: 'Код отправлен', expires_in: 300 })
  }),

  http.post(`${BASE}/auth/email-code/verify/`, async ({ request }) => {
    await delay(400)
    const body = (await request.json()) as { email?: string; code?: string }
    if (body.code !== '1234') {
      return HttpResponse.json({ detail: 'Код неверный. Проверьте письмо и введите последний код.' }, { status: 400 })
    }
    const email = body.email ?? 'user@linkavto.ru'
    currentEmail = email
    return HttpResponse.json({ token: 'mock-token', user: getOrCreateUser(email) })
  }),

  /* --- Профиль покупателя --- */

  http.get(`${BASE}/account/`, async () => {
    await delay(120)
    if (!currentEmail) return new HttpResponse(null, { status: 401 })
    return HttpResponse.json(getOrCreateUser(currentEmail))
  }),

  http.patch(`${BASE}/account/`, async ({ request }) => {
    await delay(300)
    if (!currentEmail) return new HttpResponse(null, { status: 401 })
    const patch = (await request.json()) as Partial<AuthUser>
    const user = getOrCreateUser(currentEmail)
    Object.assign(user, patch)
    // Профиль считается заполненным, как только указано имя.
    user.profile_completed = Boolean((user.first_name ?? '').trim() || (user.last_name ?? '').trim())
    return HttpResponse.json(user)
  }),

  http.post(`${BASE}/cart/merge/`, async () => {
    await delay(300)
    return HttpResponse.json({ detail: 'ok' })
  }),

  http.post(`${BASE}/garage/merge/`, async () => {
    await delay(300)
    return HttpResponse.json(vehicles)
  }),

  /* --- Гараж --- */

  http.get(`${BASE}/garage/vehicles/`, async () => {
    await delay(120)
    return HttpResponse.json(vehicles)
  }),

  http.post(`${BASE}/garage/vehicles/`, async ({ request }) => {
    await delay(300)
    const body = (await request.json()) as { vin?: string; make?: string; model?: string; modification?: string }
    const vehicle: GarageVehicle = {
      id: ++vehicleSeq,
      vehicle_type: 'car' as VehicleType,
      make: body.make ?? 'Lada',
      model: body.model ?? 'Vesta',
      modification: body.modification ?? '1.6 MT (106 л.с.)',
      year: 2020,
      vin: body.vin ?? null,
      title: body.vin
        ? `Автомобиль по VIN ${body.vin.slice(-6)}`
        : `${body.make ?? 'Lada'} ${body.model ?? 'Vesta'} ${body.modification ?? ''}`.trim(),
    }
    vehicles.push(vehicle)
    return HttpResponse.json(vehicle, { status: 201 })
  }),

  http.delete(`${BASE}/garage/vehicles/:id/`, async ({ params }) => {
    await delay(150)
    const index = vehicles.findIndex((item) => item.id === Number(params['id']))
    if (index >= 0) vehicles.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  http.get(`${BASE}/garage/makes/`, async ({ request }) => {
    await delay(120)
    const kind = (new URL(request.url).searchParams.get('type') ?? 'car') as VehicleKind
    return HttpResponse.json(brandsOf(kind, null).map((brand) => ({ id: brand.id, name: brand.name })))
  }),

  http.get(`${BASE}/garage/models/`, async () => {
    await delay(120)
    return HttpResponse.json(
      modelsOf('car', 'lada').map((model) => ({ id: model.id, name: model.name })),
    )
  }),

  http.get(`${BASE}/garage/modifications/`, async () => {
    await delay(120)
    return HttpResponse.json(
      ['1.6 MT (106 л.с.)', '1.6 CVT (113 л.с.)', '1.8 MT (122 л.с.)'].map((name, index) => ({
        id: index + 1,
        name,
      })),
    )
  }),

  /* --- Прочее --- */

  http.get(`${BASE}/banners/`, async () => {
    await delay(80)
    return HttpResponse.json(banners)
  }),

  http.get(`${BASE}/home/sections/`, async () => {
    await delay(180)
    return HttpResponse.json(homeSections())
  }),

  http.get(`${BASE}/pages/:slug/`, async ({ params }) => {
    await delay(120)
    const page = staticPages[String(params['slug'])]
    if (!page) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(page)
  }),

  http.get(`${BASE}/sellers/:id/`, async ({ params }) => {
    await delay(180)
    const seller = sellers.find((item) => String(item.id) === params['id'])
    if (!seller) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json({
      seller: {
        ...seller,
        description:
          'Продаём оригинальные и проверенные аналоговые запчасти с 2014 года. Свой склад в Москве, отгрузка в день заказа, гарантия на всю продукцию.',
        city: 'Москва',
        since: '2014',
        company_name: `ООО «${seller.name}»`,
        // TODO(api): логотип и баннер витрины — из CRM. Пока фолбэки на фронте.
        avatar_url: null,
        banner_url: null,
      },
      products: products
        .filter((item) => item.id % sellers.length === seller.id % sellers.length)
        .slice(0, 12)
        .map(toListItem),
    })
  }),

  http.post(`${BASE}/orders/`, async ({ request }) => {
    await delay(600)
    const body = (await request.json()) as OrderBody
    const order = buildOrder(body)
    const email = currentEmail ?? 'guest'
    const map = loadOrders()
    map[email] = [order, ...(map[email] ?? [])]
    saveOrders(map)
    return HttpResponse.json({ id: order.id, number: order.number }, { status: 201 })
  }),

  http.get(`${BASE}/orders/`, async () => {
    await delay(200)
    const list = loadOrders()[currentEmail ?? 'guest'] ?? []
    return HttpResponse.json({ count: list.length, next: null, previous: null, results: list })
  }),

  http.get(`${BASE}/orders/:id/`, async ({ params }) => {
    await delay(150)
    const list = loadOrders()[currentEmail ?? 'guest'] ?? []
    const order = list.find((item) => String(item.id) === String(params['id']))
    if (!order) return new HttpResponse(null, { status: 404 })
    return HttpResponse.json(order)
  }),
]
