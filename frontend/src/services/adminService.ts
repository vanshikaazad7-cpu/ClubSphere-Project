import { api } from './apiClient'
import type { AnalyticsOverview, AuditLog, Paginated } from '../domain/types'

export const adminService = {
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return api.get<AnalyticsOverview>('/admin/analytics/overview')
  },

  async getAuditLogs(params: { page?: number; page_size?: number } = {}): Promise<Paginated<AuditLog>> {
    const query = new URLSearchParams()
    query.set('page', String(params.page ?? 1))
    query.set('page_size', String(params.page_size ?? 25))

    return api.get<Paginated<AuditLog>>(`/admin/audit-logs?${query.toString()}`)
  },
}
