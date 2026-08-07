import type { ReactElement } from 'react'
import {
  ArrowRight,
  Bike,
  Car,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  CircleDot,
  Copy,
  Heart,
  History,
  Home,
  Image as ImageIcon,
  Mail,
  MailCheck,
  MapPin,
  Menu,
  Minus,
  MoreHorizontal,
  Package,
  Plus,
  Search,
  Share2,
  ShoppingCart,
  SlidersHorizontal,
  Star,
  Tractor,
  Trash2,
  Truck,
  User,
  Warehouse,
  Wrench,
  X,
  type LucideIcon,
  type LucideProps,
} from 'lucide-react'

/**
 * §2, §4а: единый набор иконок — lucide-react, stroke-width 1.75 по всему проекту.
 * §10.4: иконки только из бандла (lucide бандлится), без CDN и хотлинков.
 *
 * Обёртка задаёт дефолты (размер 20, stroke 1.75, декоративность) и сохраняет
 * прежние имена `Icon*`, чтобы существующий код не переписывался поштучно.
 * Роли иконок — по карте §4а.
 */
export type IconComponent = (props: LucideProps) => ReactElement

function make(Icon: LucideIcon): IconComponent {
  return function WrappedIcon({ size = 20, strokeWidth = 1.75, ...rest }: LucideProps) {
    return <Icon size={size} strokeWidth={strokeWidth} aria-hidden focusable={false} {...rest} />
  }
}

/* --- Хром и навигация (§4а) --- */
export const IconSearch = make(Search)
export const IconHome = make(Home)
export const IconCatalog = make(Menu) // «Меню каталога» → Menu (§4а)
export const IconGarage = make(Warehouse) // «Гараж» → Warehouse (§4а)
export const IconCart = make(ShoppingCart)
export const IconUser = make(User)
export const IconHeart = make(Heart)
export const IconAddress = make(MapPin) // «Адрес» → MapPin (§4а)
export const IconMail = make(Mail)
export const IconMailCheck = make(MailCheck)
export const IconHistory = make(History) // «Недавний запрос» → History (§4а)
export const IconClose = make(X)

/* --- Управление --- */
export const IconChevronRight = make(ChevronRight)
export const IconChevronLeft = make(ChevronLeft)
export const IconChevronDown = make(ChevronDown)
export const IconPlus = make(Plus)
export const IconMinus = make(Minus)
export const IconCheck = make(Check)
export const IconCompatOk = make(CircleCheck) // «Совместимость ок» → CircleCheck (§4а)
export const IconCopy = make(Copy) // «Копировать артикул» → Copy (§4а)
export const IconFilter = make(SlidersHorizontal)
export const IconStar = make(Star)
export const IconTrash = make(Trash2)
export const IconMore = make(MoreHorizontal) // «ещё действия» — меню-троеточие
export const IconPackage = make(Package) // пункт выдачи на карте
export const IconPhoto = make(ImageIcon) // плейсхолдер «нет фото» (§6)
export const IconShare = make(Share2)
export const IconArrowRight = make(ArrowRight) // «весь раздел» → ArrowRight (§4а)

/* --- Типы техники (§4а) --- */
export const IconTypeCar = make(Car)
export const IconTypeTruck = make(Truck)
export const IconTypeMoto = make(Bike)
export const IconTypeSpecial = make(Tractor)
export const IconTypeTires = make(CircleDot)
export const IconTypeService = make(Wrench)
