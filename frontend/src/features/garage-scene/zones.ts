/** §4а: зоны деталей — навигация, а не декорация. Один источник для SVG и 3D. */
export interface GarageZone {
  id: string
  label: string
  /** Слаг подкатегории каталога. */
  categorySlug: string
  /** Позиция чипа в процентах от габаритов SVG-сцены (0–100). */
  x: number
  y: number
  /** Точка привязки на 3D-модели; drei Html проецирует её в 2D. */
  anchor: [number, number, number]
  /** Группа полигонов модели, подсвечиваемая при hover чипа. */
  group: ModelGroup
}

export type ModelGroup = 'body' | 'glass' | 'wheels' | 'brakes' | 'hood'

export const GARAGE_ZONES: GarageZone[] = [
  { id: 'engine', label: 'Двигатель', categorySlug: 'dvigatel', x: 24, y: 34, anchor: [1.7, 0.75, 0], group: 'hood' },
  { id: 'brakes', label: 'Тормоза', categorySlug: 'tormoznaya-sistema', x: 16, y: 72, anchor: [1.2, 0.35, 0.95], group: 'brakes' },
  { id: 'suspension', label: 'Подвеска', categorySlug: 'podveska', x: 50, y: 84, anchor: [0, 0.3, 1], group: 'wheels' },
  { id: 'filters', label: 'Фильтры', categorySlug: 'filtry', x: 40, y: 22, anchor: [0.9, 0.95, 0.5], group: 'hood' },
  { id: 'body', label: 'Кузов', categorySlug: 'kuzov', x: 78, y: 30, anchor: [-1.7, 1, 0], group: 'body' },
  { id: 'electrics', label: 'Электрика', categorySlug: 'elektrika', x: 84, y: 66, anchor: [-0.4, 1.4, 0.6], group: 'glass' },
]
