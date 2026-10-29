import { api } from './apiClient'
import type { Club, MembershipJoinResponse, Paginated } from '../domain/types'

export interface GetClubsParams {
  search?: string
  branch_id?: string
  program_id?: string
  status?: string
  page?: number
  page_size?: number
}

export const clubService = {
  async getClubs(params: GetClubsParams = {}): Promise<Paginated<Club>> {
    const query = new URLSearchParams()
    query.set('page', String(params.page ?? 1))
    query.set('page_size', String(params.page_size ?? 50))
    if (params.search?.trim()) query.set('search', params.search.trim())
    if (params.status) query.set('status', params.status)
    if (params.program_id) query.set('program_id', params.program_id)
    else if (params.branch_id) query.set('branch_id', params.branch_id)

    return api.get<Paginated<Club>>(`/clubs?${query.toString()}`)
  },

  async getClub(clubId: number): Promise<Club> {
    return api.get<Club>(`/clubs/${clubId}`)
  },

  async requestJoinClub(clubId: number): Promise<MembershipJoinResponse> {
    return api.post<MembershipJoinResponse>(`/clubs/${clubId}/join`)
  },
}
