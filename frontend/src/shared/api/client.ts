import ky, { HTTPError } from 'ky'
import { API_BASE_URL } from '@/shared/config'

/** Единственный HTTP-клиент приложения (§2). */
export const api = ky.create({
  prefixUrl: API_BASE_URL,
  credentials: 'include',
  retry: { limit: 1, methods: ['get'] },
  timeout: 15_000,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = localStorage.getItem('linkavto:token')
        if (token) request.headers.set('Authorization', `Bearer ${token}`)
      },
    ],
  },
})

export interface ApiErrorShape {
  detail?: string
  [field: string]: unknown
}

export class ApiError extends Error {
  readonly status: number
  readonly data: ApiErrorShape

  constructor(status: number, data: ApiErrorShape, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

/** Приводит любую сетевую ошибку к человекочитаемому виду (§9: что случилось + что делать). */
export async function toApiError(error: unknown): Promise<ApiError> {
  if (error instanceof HTTPError) {
    let data: ApiErrorShape = {}
    try {
      data = (await error.response.json()) as ApiErrorShape
    } catch {
      /* тело не JSON — оставляем пустым */
    }
    const message =
      typeof data.detail === 'string'
        ? data.detail
        : error.response.status >= 500
          ? 'Сервис временно недоступен. Попробуйте обновить страницу через минуту.'
          : 'Запрос не прошёл. Проверьте данные и попробуйте ещё раз.'
    return new ApiError(error.response.status, data, message)
  }
  return new ApiError(0, {}, 'Нет связи с сервером. Проверьте интернет и повторите.')
}

/** GET с типизацией и нормализацией ошибок. */
export async function get<T>(path: string, searchParams?: Record<string, string | number | boolean>): Promise<T> {
  try {
    return await api.get(path, searchParams ? { searchParams } : undefined).json<T>()
  } catch (error) {
    throw await toApiError(error)
  }
}

export async function post<T>(path: string, json?: unknown): Promise<T> {
  try {
    return await api.post(path, json === undefined ? undefined : { json }).json<T>()
  } catch (error) {
    throw await toApiError(error)
  }
}

export async function patch<T>(path: string, json?: unknown): Promise<T> {
  try {
    return await api.patch(path, json === undefined ? undefined : { json }).json<T>()
  } catch (error) {
    throw await toApiError(error)
  }
}

export async function del<T>(path: string): Promise<T> {
  try {
    return await api.delete(path).json<T>()
  } catch (error) {
    throw await toApiError(error)
  }
}
