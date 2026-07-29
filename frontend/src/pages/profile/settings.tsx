import { useRef, useState } from 'react'
import { t } from '@/shared/i18n'
import { Avatar, Button, Input, toast } from '@/shared/ui'
import { ApiError } from '@/shared/api/client'
import { MAX_AVATAR_BYTES, readImageAsDataUrl } from '@/shared/lib/file'
import { updateAccount } from '@/features/auth/api'
import { useAuthStore, userDisplayName } from '@/features/auth/store'

/** Редактирование профиля покупателя: аватар + имя/фамилия/телефон (email только чтение). */
export function Component() {
  const user = useAuthStore((state) => state.user)
  const updateUser = useAuthStore((state) => state.updateUser)
  const fileRef = useRef<HTMLInputElement>(null)

  const [form, setForm] = useState({
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    phone: user?.phone ?? '',
    avatar: (user?.avatar ?? null) as string | null,
  })
  const [pending, setPending] = useState(false)

  const pickAvatar = async (file: File | undefined) => {
    if (!file) return
    if (file.size > MAX_AVATAR_BYTES) {
      toast.error(t('profile.photoTooBig'))
      return
    }
    const dataUrl = await readImageAsDataUrl(file)
    setForm((state) => ({ ...state, avatar: dataUrl }))
  }

  const save = async () => {
    setPending(true)
    try {
      const updated = await updateAccount({
        first_name: form.first_name.trim() || null,
        last_name: form.last_name.trim() || null,
        phone: form.phone.trim() || null,
        avatar: form.avatar,
      })
      updateUser(updated)
      toast.ok(t('profile.saved'))
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t('common.errorText'))
    } finally {
      setPending(false)
    }
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        void save()
      }}
      className="flex max-w-[560px] flex-col gap-5 rounded-card bg-surface p-5 shadow-float lg:p-6"
    >
      <h2 className="text-md font-semibold">{t('profile.editTitle')}</h2>

      <div className="flex items-center gap-4">
        <Avatar src={form.avatar} name={userDisplayName(user)} size={72} />
        <div className="flex flex-col gap-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event) => void pickAvatar(event.target.files?.[0])}
          />
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={() => fileRef.current?.click()}>
              {t('profile.changePhoto')}
            </Button>
            {form.avatar ? (
              <Button type="button" variant="ghost" onClick={() => setForm((s) => ({ ...s, avatar: null }))}>
                {t('profile.removePhoto')}
              </Button>
            ) : null}
          </div>
          <span className="text-xs text-ink-muted">{t('profile.photo')} · до 5 МБ</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label={t('profile.firstName')}
          autoComplete="given-name"
          value={form.first_name}
          onChange={(event) => setForm((s) => ({ ...s, first_name: event.target.value }))}
        />
        <Input
          label={t('profile.lastName')}
          autoComplete="family-name"
          value={form.last_name}
          onChange={(event) => setForm((s) => ({ ...s, last_name: event.target.value }))}
        />
      </div>

      <Input
        label={t('profile.phone')}
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        placeholder="+7 (999) 999-99-99"
        value={form.phone}
        onChange={(event) => setForm((s) => ({ ...s, phone: event.target.value }))}
      />

      <Input label={t('auth.emailLabel')} value={user?.email ?? ''} readOnly />

      <Button type="submit" variant="primary" loading={pending} className="self-start">
        {t('profile.save')}
      </Button>
    </form>
  )
}
