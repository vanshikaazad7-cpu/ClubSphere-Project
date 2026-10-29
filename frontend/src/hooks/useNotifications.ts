import { useCallback, useEffect, useState } from 'react'
import { notificationService } from '../services/notificationService'
import type { InAppNotification } from '../domain/types'

export function useNotifications(isAuthenticated: boolean) {
  const [notifications, setNotifications] = useState<InAppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return
    setLoading(true)
    try {
      const res = await notificationService.getNotifications()
      setNotifications(res.items)
      setUnreadCount(res.unread_count)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notifications.')
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false

    notificationService
      .getNotifications()
      .then((res) => {
        if (!cancelled) {
          setNotifications(res.items)
          setUnreadCount(res.unread_count)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load notifications.')
      })

    const interval = window.setInterval(() => {
      notificationService
        .getNotifications()
        .then((res) => {
          if (!cancelled) {
            setNotifications(res.items)
            setUnreadCount(res.unread_count)
          }
        })
        .catch(() => {})
    }, 60000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [isAuthenticated])

  const markAsRead = useCallback(async (notificationId: number) => {
    try {
      await notificationService.markAsRead(notificationId)
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === notificationId ? { ...n, is_read: true } : n)),
      )
      setUnreadCount((c) => Math.max(0, c - 1))
    } catch {
      // Ignore
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationService.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // Ignore
    }
  }, [])

  return {
    notifications,
    unreadCount,
    loading,
    error,
    refreshNotifications: fetchNotifications,
    markAsRead,
    markAllAsRead,
  }
}
