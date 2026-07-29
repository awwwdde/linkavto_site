import { get, patch, post } from '@/shared/api/client'
import type { AuthUser } from '@/shared/api/types'

export interface RequestCodeResponse {
  detail: string
  expires_in: number
}

export const requestEmailCode = (email: string) => post<RequestCodeResponse>('auth/email-code/', { email })

export interface VerifyCodeResponse {
  token: string
  user: AuthUser
}

export const verifyEmailCode = (email: string, code: string) =>
  post<VerifyCodeResponse>('auth/email-code/verify/', { email, code })

/** OAuth-редиректы — бэк отдаёт готовый URL провайдера. */
export const oauthUrl = (provider: 'yandex' | 'vk') =>
  `/api/v1/auth/oauth/${provider}/?next=${encodeURIComponent(window.location.pathname)}`

/**
 * Профиль текущего покупателя.
 * TODO(api): аватар в реале — multipart на `account/avatar/`; в моке шлём его
 * data:-строкой прямо в PATCH, чтобы не тащить FormData через MSW.
 */
export type AccountPatch = Partial<
  Pick<AuthUser, 'first_name' | 'last_name' | 'phone' | 'avatar'>
>

export const fetchAccount = () => get<AuthUser>('account/')

export const updateAccount = (data: AccountPatch) => patch<AuthUser>('account/', data)
