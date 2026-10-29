import type { TokenResponse } from '../domain/types'

const API_BASE = '/api/v1'

const ACCESS_KEY = 'clubsphere_access_token'
const REFRESH_KEY = 'clubsphere_refresh_token'
const PROFILE_KEY = 'clubsphere_profile'

/** Broadcast on `window` when the session can no longer be refreshed. */
export const AUTH_EXPIRED_EVENT = 'clubsphere:auth-expired'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function saveTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(PROFILE_KEY)
}

export function readStoredProfile<T>(): T | null {
  const raw = localStorage.getItem(PROFILE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export function writeStoredProfile(profile: unknown): void {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json()
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        return detail
          .map((d) => {
            if (d && typeof d === 'object' && 'msg' in d) return String((d as { msg: unknown }).msg)
            return JSON.stringify(d)
          })
          .join(' • ')
      }
    }
  } catch {
    // Response was not JSON
  }
  return `Request failed with status ${res.status}`
}

let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null

async function refreshTokens(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise

  const refresh_token = getRefreshToken()
  if (!refresh_token) return false

  isRefreshing = true
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token }),
      })
      if (!res.ok) return false

      const data: TokenResponse = await res.json()
      saveTokens(data)
      return true
    } catch {
      return false
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()

  return refreshPromise
}

export async function request<T>(path: string, init: RequestInit = {}, allowRefresh = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const access_token = getAccessToken()
  if (access_token) {
    headers.set('Authorization', `Bearer ${access_token}`)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })

  if (res.status === 401 && allowRefresh && getRefreshToken()) {
    if (await refreshTokens()) {
      return request<T>(path, init, false)
    }
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
    throw new ApiError(401, 'Your session has expired. Please sign in again.')
  }

  if (!res.ok) {
    throw new ApiError(res.status, await readErrorMessage(res))
  }

  if (res.status === 204) {
    return undefined as T
  }

  const text = await res.text()
  return (text ? JSON.parse(text) : undefined) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

/** Best-effort server-side revocation; local session is cleared regardless. */
export async function revokeSession(): Promise<void> {
  try {
    await api.post<{ message: string }>('/auth/logout')
  } catch {
    // Ignore: the token may already be invalid.
  }
}
