import { post } from '@/shared/api/client'
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
