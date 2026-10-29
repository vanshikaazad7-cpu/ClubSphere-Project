import { api } from './apiClient'
import type { EventItem, Paginated, RegistrationResponse } from '../domain/types'

export interface GetEventsParams {
  search?: string
  status?: string
  club_id?: number
  page?: number
  page_size?: number
}

export const eventService = {
  async getEvents(params: GetEventsParams = {}): Promise<Paginated<EventItem>> {
    const query = new URLSearchParams()
    query.set('page', String(params.page ?? 1))
    query.set('page_size', String(params.page_size ?? 50))
    if (params.search?.trim()) query.set('search', params.search.trim())
    if (params.status) query.set('status', params.status)
    if (params.club_id) query.set('club_id', String(params.club_id))

    return api.get<Paginated<EventItem>>(`/events?${query.toString()}`)
  },

  async getMyRegistrations(): Promise<RegistrationResponse[]> {
    return api.get<RegistrationResponse[]>('/events/my-registrations')
  },

  async registerForEvent(eventId: number): Promise<RegistrationResponse> {
    return api.post<RegistrationResponse>(`/events/${eventId}/register`)
  },

  async cancelRegistration(eventId: number): Promise<{ message: string; event_id: number }> {
    return api.del<{ message: string; event_id: number }>(`/events/${eventId}/register`)
  },
}
