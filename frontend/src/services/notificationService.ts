import { api } from './apiClient'
import type { InAppNotification, NotificationListResponse } from '../domain/types'

export const notificationService = {
  async getNotifications(): Promise<NotificationListResponse> {
    return api.get<NotificationListResponse>('/notifications')
  },

  async markAsRead(notificationId: number): Promise<InAppNotification> {
    return api.put<InAppNotification>(`/notifications/${notificationId}/read`)
  },

  async markAllAsRead(): Promise<{ message: string; updated_count: number }> {
    return api.put<{ message: string; updated_count: number }>('/notifications/read-all')
  },
}
