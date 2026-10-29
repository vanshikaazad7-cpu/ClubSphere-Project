import { api, clearSession, revokeSession, saveTokens, writeStoredProfile } from './apiClient'
import type { SessionProfile, TokenResponse, UserResponse } from '../domain/types'

export interface RegisterInput {
  full_name: string
  email: string
  password: string
  program_id?: number | null
}

export function profileFromTokens(tokens: TokenResponse): SessionProfile {
  return {
    user_id: tokens.user_id,
    full_name: tokens.full_name,
    email: tokens.email,
    role: tokens.role,
  }
}

export const authService = {
  async login(email: string, password: string): Promise<SessionProfile> {
    const tokens = await api.post<TokenResponse>('/auth/login', { email, password })
    saveTokens(tokens)
    const profile = profileFromTokens(tokens)
    writeStoredProfile(profile)
    return profile
  },

  async register(input: RegisterInput): Promise<UserResponse> {
    return api.post<UserResponse>('/auth/register', {
      full_name: input.full_name,
      email: input.email,
      password: input.password,
      ...(input.program_id ? { program_id: input.program_id } : {}),
    })
  },

  async logout(): Promise<void> {
    try {
      await revokeSession()
    } catch {
      // Best-effort logout
    } finally {
      clearSession()
    }
  },

  async getCurrentUser(): Promise<UserResponse> {
    return api.get<UserResponse>('/auth/me')
  },
}
