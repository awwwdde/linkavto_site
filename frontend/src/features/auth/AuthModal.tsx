import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { t } from '@/shared/i18n'
import { Avatar, Button, Input, Modal, toast } from '@/shared/ui'
import { SectionHeading } from '@/app/layouts/SectionHeading'
import { IconMail, IconMailCheck, IconUser } from '@/shared/ui/Icon'
import { ApiError } from '@/shared/api/client'
import { MAX_AVATAR_BYTES, readImageAsDataUrl } from '@/shared/lib/file'
import { useUiStore } from '@/app/ui-store'
import { oauthUrl, requestEmailCode, updateAccount, verifyEmailCode } from './api'
import { mergeGuestState } from './merge-guest-state'
import { useAuthStore } from './store'

const RESEND_SECONDS = 60

const emailSchema = z.object({
  email: z.email({ message: t('auth.emailInvalid') }),
})
type EmailForm = z.infer<typeof emailSchema>

type Step = 'email' | 'code' | 'register'

/** §4: авторизация — одна модалка на всё приложение, живёт в RootLayout. */
export function AuthModal() {
  const open = useUiStore((state) => state.authModalOpen)
  const close = useUiStore((state) => state.closeAuth)
  const redirectTo = useUiStore((state) => state.authRedirectTo)
  const signIn = useAuthStore((state) => state.signIn)
  const updateUser = useAuthStore((state) => state.updateUser)
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [codeError, setCodeError] = useState<string | undefined>(undefined)
  const [pending, setPending] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [reg, setReg] = useState({ first_name: '', last_name: '', phone: '', avatar: null as string | null })
  const fileRef = useRef<HTMLInputElement>(null)

  const form = useForm<EmailForm>({ resolver: zodResolver(emailSchema), defaultValues: { email: '' } })

  useEffect(() => {
    if (!open) {
      setStep('email')
      setCode('')
      setCodeError(undefined)
      setSecondsLeft(0)
      setReg({ first_name: '', last_name: '', phone: '', avatar: null })
      form.reset()
    }
  }, [open, form])

  useEffect(() => {
    if (secondsLeft <= 0) return
    const timer = window.setTimeout(() => setSecondsLeft((value) => value - 1), 1000)
    return () => window.clearTimeout(timer)
  }, [secondsLeft])

  const finish = () => {
    close()
    if (redirectTo) navigate(redirectTo)
  }

  const sendCode = async (target: string) => {
    setPending(true)
    try {
      await requestEmailCode(target)
      setEmail(target)
      setStep('code')
      setSecondsLeft(RESEND_SECONDS)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t('common.errorText'))
    } finally {
      setPending(false)
    }
  }

  const confirm = async () => {
    setPending(true)
    setCodeError(undefined)
    try {
      const result = await verifyEmailCode(email, code)
      signIn(result.user, result.token)
      await mergeGuestState()
      // Новый аккаунт — предлагаем заполнить профиль (регистрация); иначе входим.
      if (result.user.profile_completed) finish()
      else setStep('register')
    } catch (error) {
      setCodeError(error instanceof ApiError ? error.message : t('auth.codeInvalid'))
    } finally {
      setPending(false)
    }
  }

  const pickAvatar = async (file: File | undefined) => {
    if (!file) return
    if (file.size > MAX_AVATAR_BYTES) {
      toast.error(t('profile.photoTooBig'))
      return
    }
    const dataUrl = await readImageAsDataUrl(file)
    setReg((state) => ({ ...state, avatar: dataUrl }))
  }

  const submitRegister = async () => {
    setPending(true)
    try {
      const updated = await updateAccount({
        first_name: reg.first_name.trim() || null,
        last_name: reg.last_name.trim() || null,
        phone: reg.phone.trim() || null,
        avatar: reg.avatar,
      })
      updateUser(updated)
      finish()
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : t('common.errorText'))
    } finally {
      setPending(false)
    }
  }

  const headBadge = step === 'email' ? <IconMail /> : step === 'code' ? <IconMailCheck /> : <IconUser />
  const headLead =
    step === 'email' ? t('auth.heading') : step === 'code' ? t('auth.codeHeading') : t('auth.registerHeading')
  const headGhost =
    step === 'email'
      ? t('auth.headingGhost')
      : step === 'code'
        ? `${t('auth.codeHint')} ${email}`
        : t('auth.registerGhost')

  return (
    <Modal open={open} onClose={close} title={t('auth.title')} hideTitle>
      <div className="mb-6 flex flex-col gap-4">
        <span className="flex h-11 w-11 items-center justify-center rounded-control bg-ink/5 text-ink">
          {headBadge}
        </span>
        <SectionHeading size="lg" lead={headLead} ghost={headGhost} />
      </div>

      {step === 'email' ? (
        <form className="flex flex-col gap-4" onSubmit={form.handleSubmit(({ email: value }) => sendCode(value))}>
          <Input
            label={t('auth.emailLabel')}
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="name@mail.ru"
            error={form.formState.errors.email?.message}
            {...form.register('email')}
          />
          <Button type="submit" variant="primary" size="lg" block loading={pending}>
            {t('auth.sendCode')}
          </Button>

          <div className="flex items-center gap-3 py-1" aria-hidden="true">
            <span className="h-px flex-1 bg-line" />
            <span className="text-xs text-ink-muted">{t('auth.or')}</span>
            <span className="h-px flex-1 bg-line" />
          </div>

          <div className="flex flex-col gap-2">
            <OAuthButton badge="Я" label={t('auth.oauthYandex')} onClick={() => (window.location.href = oauthUrl('yandex'))} />
            <OAuthButton badge="VK" label={t('auth.oauthVk')} onClick={() => (window.location.href = oauthUrl('vk'))} />
          </div>

          <p className="text-xs leading-relaxed text-ink-muted">
            {t('auth.legal')}{' '}
            <a href="/terms" className="text-ink underline decoration-line underline-offset-2 hover:decoration-ink">
              {t('auth.legalTerms')}
            </a>
          </p>
        </form>
      ) : step === 'code' ? (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault()
            void confirm()
          }}
        >
          <div className="flex flex-col gap-2">
            <input
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
              inputMode="numeric"
              autoComplete="one-time-code"
              aria-label={t('auth.codeLabel')}
              aria-invalid={codeError ? true : undefined}
              placeholder="••••••"
              className="h-14 w-full rounded-control border border-line bg-surface text-center font-mono text-xl tracking-[0.4em] text-ink outline-none transition-[border-color] duration-[--duration-fast] placeholder:text-ink-ghost focus:border-ink-muted aria-[invalid=true]:border-danger"
            />
            {codeError ? <p className="text-sm text-danger">{codeError}</p> : null}
          </div>

          <Button type="submit" variant="primary" size="lg" block loading={pending} disabled={code.length < 4}>
            {t('auth.confirm')}
          </Button>

          <div className="flex items-center justify-between gap-4 text-sm text-ink-muted">
            <button type="button" className="hover:text-ink" onClick={() => setStep('email')}>
              {t('auth.changeEmail')}
            </button>
            {secondsLeft > 0 ? (
              <span className="tabular-nums">
                {t('auth.resendIn')} {secondsLeft}
              </span>
            ) : (
              <button type="button" className="font-medium text-ink hover:text-ink-muted" onClick={() => void sendCode(email)}>
                {t('auth.resend')}
              </button>
            )}
          </div>
        </form>
      ) : (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault()
            void submitRegister()
          }}
        >
          <div className="flex items-center gap-4">
            <Avatar src={reg.avatar} name={`${reg.first_name} ${reg.last_name}`} size={64} />
            <div className="flex flex-col gap-1">
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(event) => void pickAvatar(event.target.files?.[0])}
              />
              <Button type="button" variant="secondary" onClick={() => fileRef.current?.click()}>
                {t('auth.photoUpload')}
              </Button>
              <span className="text-xs text-ink-muted">{t('auth.photo')} · до 5 МБ</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label={t('profile.firstName')}
              autoComplete="given-name"
              value={reg.first_name}
              onChange={(event) => setReg((s) => ({ ...s, first_name: event.target.value }))}
            />
            <Input
              label={t('profile.lastName')}
              autoComplete="family-name"
              value={reg.last_name}
              onChange={(event) => setReg((s) => ({ ...s, last_name: event.target.value }))}
            />
          </div>
          <Input
            label={t('profile.phone')}
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="+7 (999) 999-99-99"
            value={reg.phone}
            onChange={(event) => setReg((s) => ({ ...s, phone: event.target.value }))}
          />

          <Button type="submit" variant="primary" size="lg" block loading={pending} disabled={!reg.first_name.trim()}>
            {t('auth.finish')}
          </Button>
          <button type="button" className="text-sm text-ink-muted hover:text-ink" onClick={finish}>
            {t('auth.skip')}
          </button>
        </form>
      )}
    </Modal>
  )
}

/** OAuth-кнопка: монохром (§3, без брендовых цветов), с буквенным бейджем провайдера. */
function OAuthButton({ badge, label, onClick }: { badge: string; label: string; onClick: () => void }) {
  return (
    <Button size="lg" block onClick={onClick} className="justify-start gap-3 px-4">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-ink/5 text-2xs font-semibold text-ink">
        {badge}
      </span>
      {label}
    </Button>
  )
}
