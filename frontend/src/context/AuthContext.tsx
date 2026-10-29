import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  AUTH_EXPIRED_EVENT,
  clearSession,
  getAccessToken,
  readStoredProfile,
} from '../services/apiClient'
import { authService, type RegisterInput } from '../services/authService'
import { AuthContext, type AuthContextValue } from './AuthContextInstance'
import type { SessionProfile } from '../domain/types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionProfile | null>(() => {
    const stored = readStoredProfile<SessionProfile>()
    return getAccessToken() ? stored : null
  })

  useEffect(() => {
    const onExpired = () => {
      clearSession()
      setUser(null)
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const profile = await authService.login(email, password)
    setUser(profile)
  }, [])

  const register = useCallback(async (input: RegisterInput) => {
    return authService.register(input)
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, login, register, logout }),
    [user, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
