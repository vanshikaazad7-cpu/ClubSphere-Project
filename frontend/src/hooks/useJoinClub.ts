import { useCallback, useEffect, useState } from 'react'
import { clubService } from '../services/clubService'
import type { Club } from '../domain/types'

export type JoinState = { kind: 'success' | 'error'; message: string } | null

export function useJoinClub(initialClubId?: string | null) {
  const [clubs, setClubs] = useState<Club[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyClubId, setBusyClubId] = useState<number | null>(null)
  const [joinState, setJoinState] = useState<Record<number, JoinState>>({})
  const [requestedClubIds, setRequestedClubIds] = useState<Set<number>>(new Set())

  const loadClubs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await clubService.getClubs({ search, status: 'active', page_size: 50 })
      setClubs(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load active clubs.')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadClubs(), 300)
    return () => window.clearTimeout(timer)
  }, [loadClubs])

  const requestToJoin = useCallback(async (club: Club) => {
    setBusyClubId(club.club_id)
    setJoinState((prev) => ({ ...prev, [club.club_id]: null }))
    try {
      await clubService.requestJoinClub(club.club_id)
      setRequestedClubIds((prev) => new Set(prev).add(club.club_id))
      setJoinState((prev) => ({
        ...prev,
        [club.club_id]: {
          kind: 'success',
          message: 'Request sent — the club manager will review your application.',
        },
      }))
    } catch (err) {
      setJoinState((prev) => ({
        ...prev,
        [club.club_id]: {
          kind: 'error',
          message: err instanceof Error ? err.message : 'Could not submit your request.',
        },
      }))
    } finally {
      setBusyClubId(null)
    }
  }, [])

  return {
    clubs,
    search,
    setSearch,
    loading,
    error,
    busyClubId,
    joinState,
    requestedClubIds,
    requestToJoin,
    initialClubId,
  }
}
