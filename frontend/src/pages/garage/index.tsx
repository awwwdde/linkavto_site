import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { t } from '@/shared/i18n'
import { Badge, Button, Container, EmptyState, Modal, PageMeta, toast } from '@/shared/ui'
import { IconPlus, IconTrash } from '@/shared/ui/Icon'
import { GarageZonesMap } from '@/features/garage/GarageZonesMap'
import { GarageVehicleForm } from '@/features/garage/GarageVehicleForm'
import { deleteGarageVehicle } from '@/features/garage/api'
import { useActiveVehicle, useGarageStore } from '@/features/garage/store'
import { useAuthStore } from '@/features/auth/store'
import { useUiStore } from '@/app/ui-store'

export function Component() {
  const user = useAuthStore((state) => state.user)
  const openAuth = useUiStore((state) => state.openAuth)
  const [formOpen, setFormOpen] = useState(false)
  const vehicles = useGarageStore((state) => state.vehicles)
  const activeId = useGarageStore((state) => state.activeVehicleId)
  const setActive = useGarageStore((state) => state.setActive)
  const removeVehicle = useGarageStore((state) => state.removeVehicle)
  const active = useActiveVehicle()

  const remove = useMutation({
    mutationFn: deleteGarageVehicle,
    onSuccess: (_data, id) => removeVehicle(id),
    onError: () => toast.error('Удалить не вышло. Повторите через минуту.'),
  })

  // §7: гараж привязан к аккаунту — весь маршрут закрыт для гостя.
  useEffect(() => {
    if (!user) openAuth('/garage')
  }, [user, openAuth])

  if (!user) {
    return (
      <Container className="py-12">
        <PageMeta title="Гараж — LINKAVTO" canonicalPath="/garage" noIndex />
        <EmptyState
          title={t('auth.title')}
          text="Войдите, чтобы добавить авто и подобрать детали под него."
          action={
            <Button variant="primary" onClick={() => openAuth('/garage')}>
              {t('nav.login')}
            </Button>
          }
        />
      </Container>
    )
  }

  return (
    <>
      <PageMeta
        title="Гараж — LINKAVTO"
        description="Добавьте автомобиль в гараж, и каталог покажет только подходящие запчасти."
        canonicalPath="/garage"
      />

      <Container className="flex flex-col gap-8 py-6 lg:py-10">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-xl font-semibold lg:text-2xl">{t('garage.title')}</h1>
          <Button variant="primary" onClick={() => setFormOpen(true)}>
            <IconPlus width={18} height={18} />
            {t('garage.addShort')}
          </Button>
        </div>

        {vehicles.length === 0 ? (
          <EmptyState
            title={t('garage.empty')}
            text={t('garage.emptyText')}
            action={
              <Button variant="primary" size="lg" onClick={() => setFormOpen(true)}>
                {t('garage.add')}
              </Button>
            }
          />
        ) : (
          <>
            {/* §3.4, правило одной оси: доминанта гаража — интерактивная схема зон. */}
            <section className="flex flex-col gap-5 rounded-card bg-surface p-6 shadow-float lg:p-10">
              <div className="flex flex-col gap-1 text-center">
                <p className="text-md font-semibold">{active?.title}</p>
                <p className="text-sm text-ink-muted">{t('garage.zonesHint')}</p>
              </div>
              <GarageZonesMap vehicle={active} className="py-2" />
            </section>

            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {vehicles.map((vehicle) => (
                <li
                  key={vehicle.id}
                  className="flex items-start justify-between gap-3 rounded-card bg-surface p-4 shadow-float"
                >
                  <div className="flex min-w-0 flex-col gap-2">
                    <span className="truncate text-base font-medium">{vehicle.title}</span>
                    {vehicle.vin ? <span className="font-mono text-sm text-ink-muted">{vehicle.vin}</span> : null}
                    {vehicle.id === activeId ? (
                      <Badge tone="ok">{t('garage.active')}</Badge>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setActive(vehicle.id)}
                        className="self-start text-sm text-ink-muted underline hover:text-ink"
                      >
                        {t('garage.setActive')}
                      </button>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => remove.mutate(vehicle.id)}
                    aria-label={t('garage.remove')}
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control text-ink-muted hover:text-danger"
                  >
                    <IconTrash />
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </Container>

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={t('garage.add')}>
        <GarageVehicleForm onDone={() => setFormOpen(false)} />
      </Modal>
    </>
  )
}
