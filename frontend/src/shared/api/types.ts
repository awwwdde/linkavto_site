/**
 * Типы API-контракта (§5 ТЗ). Пишутся вручную до появления OpenAPI-схемы
 * бэка (drf-spectacular) — после её появления генерируются openapi-typescript.
 * Деньги везде — целое число КОПЕЕК.
 */

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ImageSet {
  thumb: string
  card: string
  full: string
  alt: string
}

export type VehicleType = 'car' | 'truck' | 'moto' | 'special' | 'tires' | 'service'

/**
 * Типы транспорта в смысле Django-модели Product.vehicle_type — по ним идёт
 * каскад «класс → марка → модель → поколение → модификация».
 */
export type VehicleKind = 'car' | 'truck' | 'moto' | 'special'

/** Разделы витрины: Category.show_in на бэке. */
export type ShowIn =
  | 'cars'
  | 'trucks'
  | 'moto'
  | 'special'
  | 'accessories'
  | 'chemistry'
  | 'tools'
  | 'tires'
  | 'electrics'
  | 'dlya-to'

/**
 * Каждый вариант несёт своих предков — это позволяет выбрать любой шаг
 * подбора первым, а остальные достроить автоматически.
 */
interface VehicleOptionBase {
  id: number
  name: string
  slug: string
  vehicle_type: VehicleKind
}

/** Класс/тип техники: CarType «седан, хэтчбек», TruckType, MotoType, SpecialType. */
export type VehicleClassOption = VehicleOptionBase

export interface VehicleBrandOption extends VehicleOptionBase {
  models_count: number
  /** Классы, в которых встречается марка. */
  class_slugs: string[]
}

export interface VehicleModelOption extends VehicleOptionBase {
  brand_slug: string
  brand_name: string
  year_start: number | null
  year_end: number | null
}

export interface VehicleGenerationOption extends VehicleOptionBase {
  brand_slug: string
  model_slug: string
  model_name: string
  year_start: number | null
  year_end: number | null
}

export interface VehicleModificationOption extends VehicleOptionBase {
  brand_slug: string
  model_slug: string
  generation_slug: string
  generation_name: string
  engine: string | null
  power: number | null
}

export interface CategoryBrief {
  id: number
  name: string
  /** Слаг глобально уникален (Category.slug unique=True) — по нему и резолвится категория. */
  slug: string
  /** Полный путь предков для ссылки: `legkovye/dvigatel/sistema-pitaniya`. */
  path: string
  /** 1 — корень. Дерево поддерживает до 5 уровней. */
  level: number
  products_count: number
}

export interface CategoryNode extends CategoryBrief {
  vehicle_type: VehicleType | null
  show_in: ShowIn | null
  icon: string | null
  has_children: boolean
  children: CategoryNode[]
}

export interface CategoryDetail extends CategoryBrief {
  vehicle_type: VehicleType | null
  show_in: ShowIn | null
  description: string | null
  breadcrumbs: CategoryBrief[]
  children: CategoryBrief[]
  /** Соседи по уровню — для быстрого переключения внутри родителя. */
  siblings: CategoryBrief[]
}

export interface ProductListItem {
  id: number
  name: string
  slug: string
  sku: string
  /** Копейки. */
  price: number
  /** Копейки, до скидки. */
  old_price: number | null
  /** Считает бэк. */
  discount_percent: number | null
  image: ImageSet | null
  rating: number | null
  reviews_count: number
  in_stock: boolean
  offers_count: number
  manufacturer: string | null
  /** Приходит только когда задан garage_vehicle_id. */
  fits_vehicle: boolean | null
}

export interface ProductAttribute {
  name: string
  value: string
}

export interface CrossReference {
  sku: string
  manufacturer: string
  product_slug: string | null
}

export interface ProductDetail extends ProductListItem {
  images: ImageSet[]
  description_html: string
  description_plain: string
  oem_number: string | null
  crosses: CrossReference[]
  compatibility: string[]
  attributes: ProductAttribute[]
  category: CategoryBrief
  breadcrumbs: CategoryBrief[]
}

export interface SellerBrief {
  id: number
  name: string
  slug: string
  rating: number | null
  reviews_count: number
}

export interface Offer {
  id: number
  seller: SellerBrief
  manufacturer: string
  /** Копейки. */
  price: number
  /** Срок поставки в днях. */
  delivery_days: number
  stock: number
  is_original: boolean
}

export interface PriceHistogramBucket {
  /** Копейки — левая граница бакета. */
  from: number
  to: number
  count: number
}

export interface FacetOption {
  value: string
  label: string
  count: number
}

/**
 * Атрибутный фасет категории (§5, аналог динамических фильтров старого каталога:
 * «Вязкость», «Объём», «Материал», «Напряжение», «Сезонность» и т.п.).
 * `code` — имя GET-параметра фильтра (напр. `attr_country`), значения мультивыбором CSV.
 */
export interface AttributeFacet {
  code: string
  label: string
  options: FacetOption[]
}

export interface ProductListResponse extends Paginated<ProductListItem> {
  /** 20 бакетов min–max по текущей выборке (§5). */
  price_histogram: PriceHistogramBucket[]
  facets: {
    /** Производитель детали (Manufacturer). */
    manufacturers: FacetOption[]
    /** Бренд товара (ProductBrand). */
    product_brands: FacetOption[]
    price_min: number
    price_max: number
    /** Профильные фасеты приходят только в категориях шин и дисков. */
    tire_wheel: TireWheelFacets | null
    /** Динамические атрибутные фильтры категории (§5). */
    attributes: AttributeFacet[]
  }
}

export interface TireWheelFacets {
  tire_diameter: FacetOption[]
  tire_width: FacetOption[]
  tire_height: FacetOption[]
  tire_seasonality: FacetOption[]
  wheel_diameter: FacetOption[]
  wheel_width: FacetOption[]
  wheel_pcd: FacetOption[]
  wheel_offset_type: FacetOption[]
  wheel_type: FacetOption[]
}

export type SearchMode = 'auto' | 'vin' | 'sku' | 'text'

export interface SearchSuggestion {
  type: 'product' | 'category' | 'sku'
  title: string
  subtitle: string | null
  url: string
}

export interface SearchResponse extends Paginated<ProductListItem> {
  /** Как бэк в итоге распознал запрос. */
  resolved_mode: Exclude<SearchMode, 'auto'>
  vehicle: GarageVehicle | null
  categories: CategoryBrief[]
}

export interface GarageVehicle {
  id: number
  vehicle_type: VehicleType
  make: string
  model: string
  modification: string
  year: number | null
  vin: string | null
  title: string
}

export interface GarageOption {
  id: number
  name: string
}

export interface CartItem {
  id: number
  product: ProductListItem
  offer: Offer | null
  quantity: number
  /** Копейки за штуку. */
  price: number
  total: number
}

export interface CartSellerGroup {
  seller: SellerBrief
  items: CartItem[]
  /** Копейки. */
  subtotal: number
  delivery: number
}

export interface Cart {
  groups: CartSellerGroup[]
  items_count: number
  /** Копейки. */
  subtotal: number
  delivery: number
  total: number
}

export type OrderStatus = 'new' | 'paid' | 'shipping' | 'done' | 'canceled'

export interface Order {
  id: number
  number: string
  status: OrderStatus
  status_display: string
  created_at: string
  /** Копейки. */
  total: number
  items: CartItem[]
  delivery_address: string | null
  delivery_method: 'cdek' | 'post' | 'pickup'
  payment_method: 'card' | 'sbp' | 'cash'
}

export interface Review {
  id: number
  author: string
  rating: number
  text: string
  created_at: string
}

export interface Banner {
  id: number
  title: string
  subtitle: string | null
  image: ImageSet | null
  url: string
}

export interface HomeSection {
  id: string
  title: string
  url: string | null
  products: ProductListItem[]
}

export interface StaticPage {
  slug: string
  title: string
  html: string
  updated_at: string
}

export type DeliveryType = 'courier' | 'pickup'
export type PickupProvider = 'cdek' | 'boxberry' | 'post' | 'yandex'

/** Адрес доставки покупателя (accounts.Address). */
export interface Address {
  id: number
  /** Ярлык: «Дом», «Работа». */
  title: string
  delivery_type: DeliveryType
  /** Полный адрес для курьера. */
  full_address: string
  postal_code: string
  comment: string
  /** Для ПВЗ. */
  pickup_provider: PickupProvider | null
  pickup_point_name: string | null
  is_default: boolean
}

export interface AuthUser {
  id: number
  email: string
  first_name: string | null
  last_name: string | null
  phone: string | null
  /** URL или data:-строка (мок). */
  avatar: string | null
  /** false для только что созданного аккаунта — фронт показывает шаг регистрации. */
  profile_completed: boolean
}
