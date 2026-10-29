import { useCallback, useEffect, useState } from 'react'
import { adminService } from '../services/adminService'
import { proposalService, type ReviewDecision } from '../services/proposalService'
import { canReviewProposals, canViewAnalytics, canViewAuditLogs } from '../domain/permissions'
import { validateReviewDecision } from '../domain/validation'
import type { AnalyticsOverview, AuditLog, Proposal, SessionProfile } from '../domain/types'

export function useAdminDashboard(user: SessionProfile | null) {
  const allowedAnalytics = canViewAnalytics(user)
  const allowedAudit = canViewAuditLogs(user)
  const allowedReview = canReviewProposals(user)

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(allowedAnalytics)

  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [auditError, setAuditError] = useState<string | null>(null)
  const [loadingAudit, setLoadingAudit] = useState(allowedAudit)

  const [proposals, setProposals] = useState<Proposal[]>([])
  const [proposalsTotal, setProposalsTotal] = useState(0)
  const [proposalsError, setProposalsError] = useState<string | null>(null)
  const [loadingProposals, setLoadingProposals] = useState(allowedReview)
  const [statusFilter, setStatusFilter] = useState('')

  const [reviewingId, setReviewingId] = useState<number | null>(null)
  const [reviewErrors, setReviewErrors] = useState<Record<number, string | null>>({})
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null)
  const [comments, setComments] = useState<Record<number, string>>({})

  // Fetch Analytics
  useEffect(() => {
    if (!allowedAnalytics) return
    let cancelled = false
    adminService
      .getAnalyticsOverview()
      .then((res) => {
        if (!cancelled) {
          setOverview(res)
          setAnalyticsError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setAnalyticsError(err instanceof Error ? err.message : 'Failed to load analytics.')
      })
      .finally(() => {
        if (!cancelled) setLoadingAnalytics(false)
      })

    return () => {
      cancelled = true
    }
  }, [allowedAnalytics])

  // Fetch Audit Logs
  useEffect(() => {
    if (!allowedAudit) return
    let cancelled = false
    adminService
      .getAuditLogs({ page: 1, page_size: 25 })
      .then((res) => {
        if (!cancelled) {
          setAuditLogs(res.items)
          setAuditError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setAuditError(err instanceof Error ? err.message : 'Failed to load audit logs.')
      })
      .finally(() => {
        if (!cancelled) setLoadingAudit(false)
      })

    return () => {
      cancelled = true
    }
  }, [allowedAudit])

  // Fetch Proposals
  const refreshProposals = useCallback(async (filter: string) => {
    if (!allowedReview) return
    setLoadingProposals(true)
    try {
      const res = await proposalService.getProposals({ status: filter || undefined, page: 1, page_size: 50 })
      setProposals(res.items)
      setProposalsTotal(res.total)
      setProposalsError(null)
    } catch (err) {
      setProposalsError(err instanceof Error ? err.message : 'Failed to load club applications.')
    } finally {
      setLoadingProposals(false)
    }
  }, [allowedReview])

  useEffect(() => {
    if (!allowedReview) return
    let cancelled = false
    proposalService
      .getProposals({ status: statusFilter || undefined, page: 1, page_size: 50 })
      .then((res) => {
        if (!cancelled) {
          setProposals(res.items)
          setProposalsTotal(res.total)
          setProposalsError(null)
          setLoadingProposals(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setProposalsError(err instanceof Error ? err.message : 'Failed to load club applications.')
          setLoadingProposals(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [allowedReview, statusFilter])

  const setComment = useCallback((proposalId: number, value: string) => {
    setComments((prev) => ({ ...prev, [proposalId]: value }))
  }, [])

  const handleReview = useCallback(async (proposal: Proposal, decision: ReviewDecision) => {
    const comment = (comments[proposal.proposal_id] ?? '').trim()
    const errorMsg = validateReviewDecision(decision, comment)
    if (errorMsg) {
      setReviewErrors((prev) => ({ ...prev, [proposal.proposal_id]: errorMsg }))
      return
    }

    setReviewingId(proposal.proposal_id)
    setReviewErrors((prev) => ({ ...prev, [proposal.proposal_id]: null }))
    setReviewSuccess(null)

    try {
      await proposalService.reviewProposal(proposal.proposal_id, {
        decision,
        comment: comment || null,
      })

      setReviewSuccess(
        decision === 'approve'
          ? `“${proposal.proposed_name}” was approved — the club is now chartered and its applicant appointed Lead.`
          : decision === 'reject'
            ? `“${proposal.proposed_name}” was rejected. The applicant has been notified.`
            : `Changes were requested on “${proposal.proposed_name}”. The applicant has been notified.`,
      )
      setComments((prev) => ({ ...prev, [proposal.proposal_id]: '' }))

      // Refresh proposals and analytics
      await refreshProposals(statusFilter)
      if (allowedAnalytics) {
        const res = await adminService.getAnalyticsOverview()
        setOverview(res)
      }
    } catch (err) {
      setReviewErrors((prev) => ({
        ...prev,
        [proposal.proposal_id]: err instanceof Error ? err.message : 'Failed to record the decision.',
      }))
    } finally {
      setReviewingId(null)
    }
  }, [comments, refreshProposals, statusFilter, allowedAnalytics])

  return {
    allowedAnalytics,
    allowedAudit,
    allowedReview,
    overview,
    analyticsError,
    loadingAnalytics,
    auditLogs,
    auditError,
    loadingAudit,
    proposals,
    proposalsTotal,
    proposalsError,
    loadingProposals,
    statusFilter,
    setStatusFilter,
    reviewingId,
    reviewErrors,
    reviewSuccess,
    comments,
    setComment,
    handleReview,
  }
}
