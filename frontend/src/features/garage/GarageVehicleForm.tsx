import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import type { GarageVehicle } from '@/shared/api/types'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { Button, Input, Select, Tabs, toast } from '@/shared/ui'
import { ApiError } from '@/shared/api/client'
import { isValidVin } from '@/features/search/detect'
import { createGarageVehicle, fetchMakes, fetchModels, fetchModifications } from './api'
import { useGarageStore } from './store'

type Mode = 'model' | 'vin'

export function GarageVehicleForm({ onDone }: { onDone?: () => void }) {
  const [mode, setMode] = useState<Mode>('model')
  const [makeId, setMakeId] = useState<number | null>(null)
  const [modelId, setModelId] = useState<number | null>(null)
  const [modificationId, setModificationId] = useState<number | null>(null)
  const [vin, setVin] = useState('')
  const [vinError, setVinError] = useState<string | undefined>(undefined)
  const addVehicle = useGarageStore((state) => state.addVehicle)

  const makes = useQuery({ queryKey: queryKeys.garage.makes('car'), queryFn: () => fetchMakes('car') })
  const models = useQuery({
    queryKey: queryKeys.garage.models(makeId),
    queryFn: () => fetchModels(makeId!),
    enabled: makeId !== null,
  })
  const modifications = useQuery({
    queryKey: queryKeys.garage.modifications(modelId),
    queryFn: () => fetchModifications(modelId!),
    enabled: modelId !== null,
  })

  const create = useMutation({
    mutationFn: createGarageVehicle,
    onSuccess: (vehicle: GarageVehicle) => {
      addVehicle(vehicle)
      onDone?.()
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : t('common.errorText')),
  })

  const submitByModel = () => {
    if (makeId === null || modelId === null || modificationId === null) return
    create.mutate({
      vehicle_type: 'car',
      make_id: makeId,
      model_id: modelId,
      modification_id: modificationId,
    })
  }

  const submitByVin = () => {
    const value = vin.trim().toUpperCase()
    if (!isValidVin(value)) {
      setVinError(t('garage.vinInvalid'))
      return
    }
    setVinError(undefined)
    create.mutate({ vin: value })
  }

  return (
    <div className="flex flex-col gap-4">
      <Tabs
        aria-label={t('garage.add')}
        value={mode}
        onChange={setMode}
        items={[
          { value: 'model', label: t('garage.byModel') },
          { value: 'vin', label: t('garage.byVin') },
        ]}
      />

      {mode === 'model' ? (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault()
            submitByModel()
          }}
        >
          <Select
            label={t('garage.make')}
            value={makeId ?? ''}
            onChange={(event) => {
              setMakeId(Number(event.target.value))
              setModelId(null)
              setModificationId(null)
            }}
          >
            <option value="" disabled>
              —
            </option>
            {(makes.data ?? []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </Select>

          <Select
            label={t('garage.model')}
            value={modelId ?? ''}
            disabled={makeId === null}
            onChange={(event) => {
              setModelId(Number(event.target.value))
              setModificationId(null)
            }}
          >
            <option value="" disabled>
              —
            </option>
            {(models.data ?? []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </Select>

          <Select
            label={t('garage.modification')}
            value={modificationId ?? ''}
            disabled={modelId === null}
            onChange={(event) => setModificationId(Number(event.target.value))}
          >
            <option value="" disabled>
              —
            </option>
            {(modifications.data ?? []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </Select>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            block
            loading={create.isPending}
            disabled={modificationId === null}
          >
            {t('garage.add')}
          </Button>
        </form>
      ) : (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault()
            submitByVin()
          }}
        >
          <Input
            label={t('garage.vin')}
            hint={t('garage.vinHint')}
            error={vinError}
            value={vin}
            maxLength={17}
            autoCapitalize="characters"
            onChange={(event) => setVin(event.target.value.toUpperCase().replace(/\s/g, ''))}
            className="font-mono tracking-[0.15em]"
          />
          <Button type="submit" variant="primary" size="lg" block loading={create.isPending}>
            {t('garage.add')}
          </Button>
        </form>
      )}
    </div>
  )
}
