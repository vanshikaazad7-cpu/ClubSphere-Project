import { useCallback, useEffect, useState } from 'react'
import { proposalService } from '../services/proposalService'
import { validateProposalInput } from '../domain/validation'
import type { Proposal } from '../domain/types'

export function useProposals() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loadingProposals, setLoadingProposals] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [proposedName, setProposedName] = useState('')
  const [branchId, setBranchId] = useState('')
  const [programId, setProgramId] = useState('')
  const [description, setDescription] = useState('')

  const fetchProposals = useCallback(async () => {
    try {
      const res = await proposalService.getProposals({ page: 1, page_size: 50 })
      setProposals(res.items)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load your proposals.')
    } finally {
      setLoadingProposals(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    proposalService
      .getProposals({ page: 1, page_size: 50 })
      .then((res) => {
        if (!cancelled) {
          setProposals(res.items)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load your proposals.')
      })
      .finally(() => {
        if (!cancelled) setLoadingProposals(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const submitProposal = useCallback(async () => {
    setSuccess(null)
    setError(null)

    const validationError = validateProposalInput(proposedName, programId, description)
    if (validationError) {
      setError(validationError)
      return false
    }

    setSubmitting(true)
    try {
      const created = await proposalService.createProposal({
        proposed_name: proposedName.trim(),
        program_id: Number(programId),
        description: description.trim(),
      })
      setSuccess(
        `Proposal #${created.proposal_id} for “${created.proposed_name}” was submitted for Faculty review.`,
      )
      setProposedName('')
      setBranchId('')
      setProgramId('')
      setDescription('')
      setLoadingProposals(true)
      await fetchProposals()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit your proposal.')
      return false
    } finally {
      setSubmitting(false)
    }
  }, [proposedName, programId, description, fetchProposals])

  return {
    proposals,
    loadingProposals,
    error,
    success,
    submitting,
    proposedName,
    setProposedName,
    branchId,
    setBranchId,
    programId,
    setProgramId,
    description,
    setDescription,
    submitProposal,
    refreshProposals: fetchProposals,
  }
}
