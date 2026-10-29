import { useCallback, useEffect, useState } from 'react'
import { eventService } from '../services/eventService'
import type { EventItem } from '../domain/types'

export type EventFeedback = { kind: 'success' | 'error'; message: string } | null

export function useEvents() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('published')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyEventId, setBusyEventId] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<Record<number, EventFeedback>>({})
  const [registeredIds, setRegisteredIds] = useState<Set<number>>(new Set())

  // Load existing registrations for this student on mount
  useEffect(() => {
    let cancelled = false
    eventService
      .getMyRegistrations()
      .then((myRegs) => {
        if (!cancelled) {
          setRegisteredIds(new Set(myRegs.map((r) => r.event_id)))
        }
      })
      .catch(() => {
        // Non-blocking
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Load events when search or status filters change
  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      eventService
        .getEvents({ search, status, page_size: 50 })
        .then((res) => {
          if (!cancelled) {
            setEvents(res.items)
            setError(null)
            setLoading(false)
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : 'Failed to load events.')
            setLoading(false)
          }
        })
    }, 300)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [search, status])

  const refreshEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await eventService.getEvents({ search, status, page_size: 50 })
      setEvents(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events.')
    } finally {
      setLoading(false)
    }
  }, [search, status])

  const toggleRegistration = useCallback(async (event: EventItem) => {
    setBusyEventId(event.event_id)
    setFeedback((prev) => ({ ...prev, [event.event_id]: null }))
    const isRegistered = registeredIds.has(event.event_id)

    try {
      if (isRegistered) {
        await eventService.cancelRegistration(event.event_id)
        setRegisteredIds((prev) => {
          const next = new Set(prev)
          next.delete(event.event_id)
          return next
        })
        setFeedback((prev) => ({
          ...prev,
          [event.event_id]: { kind: 'success', message: 'Your registration was cancelled.' },
        }))
      } else {
        await eventService.registerForEvent(event.event_id)
        setRegisteredIds((prev) => new Set(prev).add(event.event_id))
        setFeedback((prev) => ({
          ...prev,
          [event.event_id]: { kind: 'success', message: 'You are registered for this event.' },
        }))
      }
      await refreshEvents()
    } catch (err) {
      setFeedback((prev) => ({
        ...prev,
        [event.event_id]: {
          kind: 'error',
          message: err instanceof Error ? err.message : 'Registration action failed.',
        },
      }))
    } finally {
      setBusyEventId(null)
    }
  }, [registeredIds, refreshEvents])

  return {
    events,
    search,
    setSearch,
    status,
    setStatus,
    loading,
    error,
    busyEventId,
    feedback,
    registeredIds,
    toggleRegistration,
    refreshEvents,
  }
}
