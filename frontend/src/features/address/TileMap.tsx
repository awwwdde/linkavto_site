import { useEffect, useLayoutEffect, useRef, useState, type PointerEvent, type ReactNode } from 'react'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { IconMinus, IconPlus } from '@/shared/ui/Icon'

export interface LatLng {
  lat: number
  lng: number
}

export interface MapMarker {
  id: string
  position: LatLng
  label: string
  active?: boolean
  icon?: ReactNode
  onSelect?: () => void
}

const TILE = 256
const MIN_ZOOM = 4
const MAX_ZOOM = 18

const worldSize = (zoom: number) => TILE * 2 ** zoom

const lngToX = (lng: number, zoom: number) => ((lng + 180) / 360) * worldSize(zoom)

const latToY = (lat: number, zoom: number) => {
  const sin = Math.sin((lat * Math.PI) / 180)
  return (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * worldSize(zoom)
}

const xToLng = (x: number, zoom: number) => (x / worldSize(zoom)) * 360 - 180

const yToLat = (y: number, zoom: number) => {
  const n = Math.PI - (2 * Math.PI * y) / worldSize(zoom)
  return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)))
}

/** Раскладка по хостам 2ГИС — как в их растровом API. */
const tileUrl = (x: number, y: number, z: number) =>
  `https://tile${(x + y) % 4}.maps.2gis.com/tiles?x=${x}&y=${y}&z=${z}&v=1`

interface TileMapProps {
  center: LatLng
  zoom?: number
  markers?: MapMarker[]
  /** Метка выбранного адреса (режим доставки). */
  pin?: LatLng | null
  /** Клик по карте без перетаскивания. */
  onPick?: (position: LatLng) => void
  /** Панель поверх карты справа сверху. */
  overlay?: ReactNode
  className?: string
}

/**
 * Карта на растровых тайлах 2ГИС: перетаскивание, зум, слой меток.
 * Без сторонних SDK — проекция Web Mercator считается здесь же, поэтому нет ни
 * ключа API, ни внешнего JS; наружу тянутся только картинки тайлов.
 */
export function TileMap({ center, zoom: initialZoom = 11, markers = [], pin, onPick, overlay, className }: TileMapProps) {
  const box = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })
  /**
   * Вид карты одним состоянием: зум и центр в мировых пикселях этого зума.
   * Раздельными состояниями их держать нельзя — при смене зума координаты
   * пересчитываются вместе с ним, иначе вид разъезжается.
   */
  const [view, setView] = useState(() => ({
    zoom: initialZoom,
    x: lngToX(center.lng, initialZoom),
    y: latToY(center.lat, initialZoom),
  }))
  const { zoom } = view
  const drag = useRef<{ pointerId: number; startX: number; startY: number; worldX: number; worldY: number; moved: boolean } | null>(null)
  // Активные касания и текущий щипок — для зума двумя пальцами.
  const pointers = useRef(new Map<number, { x: number; y: number }>())
  const pinch = useRef<{ distance: number; zoomed: boolean } | null>(null)

  const pointerDistance = () => {
    const [a, b] = [...pointers.current.values()]
    if (!a || !b) return 0
    return Math.hypot(a.x - b.x, a.y - b.y)
  }

  useLayoutEffect(() => {
    const node = box.current
    if (!node) return
    // Первый замер синхронный: ResizeObserver привязан к отрисовке кадра и в
    // фоновой вкладке не сработает — карта осталась бы пустой.
    const rect = node.getBoundingClientRect()
    setSize({ width: rect.width, height: rect.height })

    const observer = new ResizeObserver(([entry]) => {
      const next = entry?.contentRect
      if (next) setSize({ width: next.width, height: next.height })
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  // Карта открывается на переданном центре и следует за ним при смене режима.
  useEffect(() => {
    setView((state) => ({
      ...state,
      x: lngToX(center.lng, state.zoom),
      y: latToY(center.lat, state.zoom),
    }))
  }, [center.lat, center.lng])

  /**
   * Смена уровня зума. `anchor` — смещение точки притяжения от центра карты в
   * пикселях: при зуме колесом под курсором остаётся то же место.
   */
  const changeZoom = (delta: number, anchor?: { dx: number; dy: number }) => {
    const dx = anchor?.dx ?? 0
    const dy = anchor?.dy ?? 0
    setView((state) => {
      const next = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, state.zoom + delta))
      if (next === state.zoom) return state
      const factor = 2 ** (next - state.zoom)
      return { zoom: next, x: (state.x + dx) * factor - dx, y: (state.y + dy) * factor - dy }
    })
  }

  // Колесо и двойной клик — зум к курсору. Слушатель вешаем вручную: нужен
  // preventDefault, а React-обработчик wheel пассивный.
  useEffect(() => {
    const node = box.current
    if (!node) return

    const anchorOf = (clientX: number, clientY: number) => {
      const rect = node.getBoundingClientRect()
      return { dx: clientX - rect.left - rect.width / 2, dy: clientY - rect.top - rect.height / 2 }
    }

    let wheelLock = 0
    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      const now = performance.now()
      // Тачпад шлёт десятки событий на один жест — держим шаг не чаще 180 мс.
      if (now - wheelLock < 180) return
      wheelLock = now
      changeZoom(event.deltaY < 0 ? 1 : -1, anchorOf(event.clientX, event.clientY))
    }

    const onDoubleClick = (event: MouseEvent) => {
      event.preventDefault()
      changeZoom(1, anchorOf(event.clientX, event.clientY))
    }

    node.addEventListener('wheel', onWheel, { passive: false })
    // Там, где клик выбирает адрес, двойной клик не зумим: первый клик уже
    // отработал бы выбором, и приближение выглядело бы случайным.
    if (!onPick) node.addEventListener('dblclick', onDoubleClick)
    return () => {
      node.removeEventListener('wheel', onWheel)
      node.removeEventListener('dblclick', onDoubleClick)
    }
  })

  const left = view.x - size.width / 2
  const top = view.y - size.height / 2

  const screen = (position: LatLng) => ({
    x: lngToX(position.lng, zoom) - left,
    y: latToY(position.lat, zoom) - top,
  })

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
    event.currentTarget.setPointerCapture(event.pointerId)

    if (pointers.current.size === 2) {
      // Второй палец — начинается щипок, перетаскивание прекращаем.
      drag.current = null
      pinch.current = { distance: pointerDistance(), zoomed: false }
      return
    }
    drag.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      worldX: view.x,
      worldY: view.y,
      moved: false,
    }
  }

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (pointers.current.has(event.pointerId)) {
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY })
    }

    // Щипок: шаг зума, когда расстояние между пальцами изменилось заметно.
    const gesture = pinch.current
    if (gesture && pointers.current.size === 2) {
      const distance = pointerDistance()
      const ratio = distance / gesture.distance
      if (ratio > 1.6 || ratio < 0.65) {
        changeZoom(ratio > 1 ? 1 : -1)
        pinch.current = { distance, zoomed: true }
      }
      return
    }

    const state = drag.current
    if (!state || state.pointerId !== event.pointerId) return
    const dx = event.clientX - state.startX
    const dy = event.clientY - state.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) state.moved = true
    setView((current) => ({ ...current, x: state.worldX - dx, y: state.worldY - dy }))
  }

  const onPointerUp = (event: PointerEvent<HTMLDivElement>) => {
    pointers.current.delete(event.pointerId)
    const gesture = pinch.current
    if (pointers.current.size < 2) pinch.current = null

    const state = drag.current
    drag.current = null
    if (gesture || !state || state.moved || !onPick) return
    const rect = box.current?.getBoundingClientRect()
    if (!rect) return
    const x = left + (event.clientX - rect.left)
    const y = top + (event.clientY - rect.top)
    onPick({ lat: yToLat(y, zoom), lng: xToLng(x, zoom) })
  }

  /**
   * Тайлы уровня `level`, отмасштабированные к текущему виду. Запас в два ряда —
   * при перетаскивании края не белеют. Уровень на единицу меньше используется
   * подложкой: пока грузятся тайлы нового зума, дырок на карте нет.
   */
  const tileLayer = (level: number) => {
    const layer: { key: string; url: string; x: number; y: number; size: number }[] = []
    if (size.width <= 0 || level < 0) return layer
    const scale = 2 ** (zoom - level)
    const tileSize = TILE * scale
    const max = 2 ** level
    const x0 = Math.floor(left / tileSize) - 2
    const y0 = Math.floor(top / tileSize) - 2
    const x1 = Math.floor((left + size.width) / tileSize) + 2
    const y1 = Math.floor((top + size.height) / tileSize) + 2
    for (let ty = y0; ty <= y1; ty += 1) {
      if (ty < 0 || ty >= max) continue
      for (let tx = x0; tx <= x1; tx += 1) {
        const wrapped = ((tx % max) + max) % max
        layer.push({
          key: `${level}:${tx}:${ty}`,
          url: tileUrl(wrapped, ty, level),
          x: tx * tileSize - left,
          y: ty * tileSize - top,
          size: tileSize,
        })
      }
    }
    return layer
  }

  const underlay = tileLayer(zoom - 1)
  const tiles = tileLayer(zoom)

  const zoomButton =
    'flex h-9 w-9 items-center justify-center rounded-full bg-surface text-ink shadow-float transition-colors duration-[--duration-fast] hover:bg-paper disabled:opacity-40'

  const pinPosition = pin ? screen(pin) : null

  return (
    <div className={cn('relative overflow-hidden rounded-card border border-line bg-paper', className)}>
      <div
        ref={box}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={(event) => {
          pointers.current.delete(event.pointerId)
          if (pointers.current.size < 2) pinch.current = null
          drag.current = null
        }}
        role="application"
        aria-label={t('address.mapAria')}
        className="absolute inset-0 touch-none select-none [cursor:grab] active:[cursor:grabbing]"
      >
        {/* Подложка предыдущего уровня — карта не белеет, пока грузится новый. */}
        {underlay.map((tile) => (
          <img
            key={tile.key}
            src={tile.url}
            alt=""
            draggable={false}
            className="pointer-events-none absolute max-w-none"
            style={{ width: tile.size, height: tile.size, transform: `translate3d(${tile.x}px, ${tile.y}px, 0)` }}
          />
        ))}

        {tiles.map((tile) => (
          <img
            key={tile.key}
            src={tile.url}
            alt=""
            draggable={false}
            className="pointer-events-none absolute max-w-none"
            style={{ width: tile.size, height: tile.size, transform: `translate3d(${tile.x}px, ${tile.y}px, 0)` }}
          />
        ))}

        {markers.map((marker) => {
          const position = screen(marker.position)
          if (position.x < -40 || position.y < -40 || position.x > size.width + 40 || position.y > size.height + 40) {
            return null
          }
          return (
            <button
              key={marker.id}
              type="button"
              aria-label={marker.label}
              aria-pressed={marker.active}
              onPointerDown={(event) => event.stopPropagation()}
              onClick={() => marker.onSelect?.()}
              style={{ transform: `translate3d(${position.x}px, ${position.y}px, 0)` }}
              className={cn(
                'absolute -ml-4 -mt-4 flex h-8 w-8 items-center justify-center rounded-control border shadow-float',
                'transition-colors duration-[--duration-fast]',
                marker.active
                  ? 'z-10 border-accent bg-accent text-white'
                  : 'border-line bg-surface text-ink hover:border-ink-muted',
              )}
            >
              {marker.icon}
            </button>
          )
        })}

        {pinPosition ? (
          <span
            style={{ transform: `translate3d(${pinPosition.x}px, ${pinPosition.y}px, 0)` }}
            className="pointer-events-none absolute -ml-4 -mt-8 text-accent drop-shadow-[0_2px_6px_rgb(0_0_0/0.35)]"
          >
            <svg width={32} height={32} viewBox="0 0 24 24" aria-hidden focusable="false">
              <path
                d="M12 22s7-6.1 7-11a7 7 0 1 0-14 0c0 4.9 7 11 7 11Z"
                fill="currentColor"
                stroke="white"
                strokeWidth={1.5}
              />
              <circle cx="12" cy="11" r="2.6" fill="white" />
            </svg>
          </span>
        ) : null}
      </div>

      <div className="pointer-events-none absolute inset-0 p-3">
        <div className="flex items-start justify-between gap-3">
          <div className="pointer-events-auto flex flex-col gap-2">
            <button
              type="button"
              onClick={() => changeZoom(1)}
              disabled={zoom >= MAX_ZOOM}
              aria-label={t('address.zoomIn')}
              className={zoomButton}
            >
              <IconPlus width={18} height={18} />
            </button>
            <button
              type="button"
              onClick={() => changeZoom(-1)}
              disabled={zoom <= MIN_ZOOM}
              aria-label={t('address.zoomOut')}
              className={zoomButton}
            >
              <IconMinus width={18} height={18} />
            </button>
          </div>

          {overlay ? <div className="pointer-events-auto">{overlay}</div> : null}
        </div>
      </div>

      <span className="pointer-events-none absolute right-2 bottom-2 rounded-control bg-surface/85 px-2 py-0.5 text-[11px] text-ink-muted">
        {t('address.mapAttribution')}
      </span>
    </div>
  )
}
