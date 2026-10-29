import { api } from './apiClient'
import type { Branch, Paginated } from '../domain/types'

export const academicService = {
  async getBranches(): Promise<Branch[]> {
    const res = await api.get<Paginated<Branch>>('/branches')
    return res.items
  },
}
