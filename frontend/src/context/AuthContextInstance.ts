import { createContext } from 'react'
import type { SessionProfile, UserResponse } from '../domain/types'
import type { RegisterInput } from '../services/authService'

export interface AuthContextValue {
  user: SessionProfile | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<UserResponse>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
