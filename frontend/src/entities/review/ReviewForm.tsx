import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Review } from '@/shared/api/types'
import { ApiError, post } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/query-keys'
import { t } from '@/shared/i18n'
import { cn } from '@/shared/lib/cn'
import { Button, toast } from '@/shared/ui'
import { IconStar } from '@/shared/ui/Icon'
import { useAuthStore } from '@/features/auth/store'
import { useUiStore } from '@/app/ui-store'

export function ReviewForm({ productSlug }: { productSlug: string }) {
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const user = useAuthStore((state) => state.user)
  const openAuth = useUiStore((state) => state.openAuth)
  const queryClient = useQueryClient()

  const submit = useMutation({
    mutationFn: () => post<Review>(`products/${productSlug}/reviews/`, { rating, text }),
    onSuccess: () => {
      setRating(0)
      setText('')
      toast.ok('Отзыв отправлен на модерацию.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.products.reviews(productSlug) })
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : t('common.errorText')),
  })

  if (!user) {
    return (
      <Button variant="secondary" onClick={() => openAuth()}>
        Войти, чтобы оставить отзыв
      </Button>
    )
  }

  return (
    <form
      className="flex flex-col gap-3 rounded-card bg-surface p-4 shadow-float"
      onSubmit={(event) => {
        event.preventDefault()
        submit.mutate()
      }}
    >
      <fieldset className="flex items-center gap-1">
        <legend className="mb-2 text-base font-semibold">Ваша оценка</legend>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => setRating(star)}
            aria-label={`${star} из 5`}
            aria-pressed={rating === star}
            className="flex h-10 w-10 items-center justify-center rounded-control text-ink"
          >
            <IconStar className={cn(star <= rating ? 'fill-current' : 'opacity-30')} />
          </button>
        ))}
      </fieldset>

      <label className="flex flex-col gap-2">
        <span className="text-sm font-medium text-ink-muted">Текст отзыва</span>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={4}
          placeholder="Подошла ли деталь, как быстро приехала, что стоит знать другим"
          className="w-full rounded-control border border-line bg-surface p-3 text-base text-ink placeholder:text-ink-muted focus:border-ink-muted focus:outline-none"
        />
      </label>

      <Button
        type="submit"
        variant="primary"
        loading={submit.isPending}
        disabled={rating === 0 || text.trim().length < 10}
      >
        Отправить отзыв
      </Button>
    </form>
  )
}
