import { useEffect, useState } from 'react'
import { clubService } from '../services/clubService'
import type { Club } from '../domain/types'

export function useClubs() {
  const [clubs, setClubs] = useState<Club[]>([])
  const [search, setSearch] = useState('')
  const [branchId, setBranchId] = useState('')
  const [programId, setProgramId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError(null)

      clubService
        .getClubs({
          search,
          branch_id: branchId,
          program_id: programId,
          page_size: 100,
        })
        .then((res) => {
          if (cancelled) return
          setClubs(res.items)
          setLoading(false)
        })
        .catch((err: unknown) => {
          if (cancelled) return
          setError(err instanceof Error ? err.message : 'Failed to load clubs.')
          setLoading(false)
        })
    }, 300)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [search, branchId, programId])

  return {
    clubs,
    search,
    setSearch,
    branchId,
    setBranchId,
    programId,
    setProgramId,
    loading,
    error,
  }
}
