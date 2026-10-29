import { useAuth } from '../hooks/useAuth'
import { useAdminDashboard } from '../hooks/useAdminDashboard'
import { formatDate } from '../lib/format'
import { PROPOSAL_STATUS_TABS } from '../domain/constants'
import { isFacultyReviewer } from '../domain/permissions'
import {
  EmptyState,
  ErrorNote,
  PageHeader,
  Spinner,
  StatusBadge,
  SuccessNote,
} from '../components/ui'
import type { Proposal } from '../domain/types'
import type { ReviewDecision } from '../services/proposalService'

function StatCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string
  value: string | number
  hint?: string
  accent: string
}) {
  return (
    <div className="rounded-2xl border border-rose/30 bg-white p-5 shadow-sm">
      <p className="text-xs uppercase tracking-wider text-olive font-medium">{label}</p>
      <p className={`mt-2 text-3xl font-extrabold ${accent}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-olive">{hint}</p>}
    </div>
  )
}

function ProposalCard({
  proposal,
  canReview,
  isFaculty,
  reviewing,
  reviewError,
  comment,
  onCommentChange,
  onReview,
}: {
  proposal: Proposal
  canReview: boolean
  isFaculty: boolean
  reviewing: boolean
  reviewError?: string | null
  comment: string
  onCommentChange: (value: string) => void
  onReview: (decision: ReviewDecision) => void
}) {
  const actionable = canReview && (proposal.status === 'submitted' || proposal.status === 'changes_requested')

  return (
    <article className="rounded-2xl border border-rose/30 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-bean">{proposal.proposed_name}</h3>
          <p className="mt-0.5 text-xs text-olive">
            by <span className="font-medium text-bean">{proposal.applicant_name ?? 'Unknown applicant'}</span>
            {' • '}
            {proposal.program_name ?? 'Unknown program'}
            {proposal.branch_name && ` (${proposal.branch_name})`}
          </p>
        </div>
        <StatusBadge status={proposal.status} />
      </div>

      <p className="mt-3 text-xs leading-relaxed text-olive">{proposal.description}</p>
      <p className="mt-2 text-[11px] text-olive">Submitted {formatDate(proposal.submitted_at)}</p>

      {proposal.approvals.length > 0 ? (
        <ol className="mt-4 space-y-2 border-t border-rose/30 pt-4">
          {proposal.approvals.map((approval) => (
            <li key={approval.approval_id} className="text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold uppercase tracking-wide text-bean">{approval.stage}</span>
                <StatusBadge status={approval.decision === 'approve' ? 'approved' : approval.decision} />
                <span className="text-olive">
                  by {approval.reviewer_name ?? 'Reviewer'} on {formatDate(approval.decided_at)}
                </span>
              </div>
              {approval.comment && (
                <p className="mt-1 rounded-lg bg-vanilla/30 px-3 py-2 text-olive">“{approval.comment}”</p>
              )}
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-4 border-t border-rose/30 pt-4 text-xs text-olive">
          Awaiting first review by a Faculty Advisor.
        </p>
      )}

      {actionable && (
        <div className="mt-4 border-t border-rose/30 pt-4">
          <label
            htmlFor={`review-comment-${proposal.proposal_id}`}
            className="mb-1.5 block text-xs font-medium text-olive"
          >
            Reviewer comment <span className="text-rose font-normal">(required to reject or request changes)</span>
          </label>
          <textarea
            id={`review-comment-${proposal.proposal_id}`}
            rows={2}
            value={comment}
            onChange={(e) => onCommentChange(e.target.value)}
            placeholder="Add your reasoning for the applicant…"
            className="w-full resize-y rounded-xl border border-rose/30 bg-white px-3 py-2 text-xs text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20"
          />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={reviewing}
              onClick={() => onReview('approve')}
              className="rounded-xl bg-olive px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-olive/90 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              {reviewing
                ? 'Recording…'
                : isFaculty
                  ? 'Recommend approval'
                  : 'Approve & charter club'}
            </button>
            <button
              type="button"
              disabled={reviewing}
              onClick={() => onReview('changes_requested')}
              className="rounded-xl border border-rose/40 bg-rose/10 px-3.5 py-2 text-xs font-semibold text-bean transition hover:bg-rose/20 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              Request changes
            </button>
            <button
              type="button"
              disabled={reviewing}
              onClick={() => onReview('reject')}
              className="rounded-xl border border-blood/40 bg-blood/10 px-3.5 py-2 text-xs font-semibold text-blood transition hover:bg-blood/20 disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              Reject
            </button>
          </div>
          {reviewError && (
            <div className="mt-3">
              <ErrorNote message={reviewError} />
            </div>
          )}
        </div>
      )}
    </article>
  )
}

export default function AdminDashboardPage() {
  const { user } = useAuth()
  const {
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
  } = useAdminDashboard(user)

  if (!allowedReview) {
    return (
      <div>
        <PageHeader title="Admin Dashboard" icon="🛡️" subtitle="Institution-wide governance and analytics." />
        <EmptyState
          title="Privileged access required"
          hint={`You are signed in as ${user?.role || 'an unprivileged user'}. Contact an administrator if you believe this is wrong.`}
        />
      </div>
    )
  }

  const attendanceRate = overview ? Math.round(overview.avg_attendance_rate * 100) : 0
  const isFaculty = isFacultyReviewer(user)

  return (
    <div>
      <PageHeader
        title="Admin Dashboard"
        icon="🛡️"
        subtitle={
          allowedAnalytics
            ? 'Institution-wide governance and analytics, calculated live from database records.'
            : 'Department club proposal review and governance.'
        }
      />

      {allowedAnalytics && (
        <>
          {loadingAnalytics && <Spinner label="Loading analytics" />}
          {analyticsError && <ErrorNote message={analyticsError} />}

          {overview && !loadingAnalytics && (
            <>
              {/* Headline metrics */}
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <StatCard
                  label="Active clubs"
                  value={overview.active_clubs}
                  hint={`${overview.total_clubs} chartered in total`}
                  accent="text-blood"
                />
                <StatCard
                  label="Pending proposals"
                  value={overview.pending_proposals}
                  hint="Awaiting Faculty or HOD review"
                  accent={overview.pending_proposals > 0 ? 'text-rose' : 'text-bean'}
                />
                <StatCard
                  label="Published events"
                  value={overview.published_events}
                  hint={`${overview.total_events} events on record`}
                  accent="text-olive"
                />
                <StatCard
                  label="Students"
                  value={overview.total_students}
                  hint="Registered student accounts"
                  accent="text-blood"
                />
              </div>

              {/* Secondary metrics */}
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <StatCard
                  label="Confirmed registrations"
                  value={overview.confirmed_registrations}
                  hint={`${overview.total_registrations} total registration attempts`}
                  accent="text-bean"
                />
                <StatCard
                  label="Attendance recorded"
                  value={overview.total_attendance}
                  hint="Verified attendance marks"
                  accent="text-bean"
                />
                <StatCard
                  label="Avg attendance rate"
                  value={`${attendanceRate}%`}
                  hint="Attendance ÷ confirmed registrations"
                  accent={attendanceRate >= 60 ? 'text-olive' : 'text-rose'}
                />
              </div>
            </>
          )}
        </>
      )}

      {/* Club applications — proposal review pipeline */}
      <section className={allowedAnalytics ? 'mt-10' : 'mt-2'}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-bean">Club applications</h2>
            <p className="mt-1 text-xs text-olive">
              Proposals to charter new student clubs.
              {isFaculty
                ? ' As a Faculty Advisor, your recommendation advances the application to the Head of Department.'
                : ' Final approval charters the club immediately and appoints the applicant as Lead.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {PROPOSAL_STATUS_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setStatusFilter(tab.key)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition cursor-pointer ${
                  statusFilter === tab.key
                    ? 'bg-blood text-white shadow-lg shadow-blood/20'
                    : 'border border-rose/30 bg-white text-olive hover:border-blood/40 hover:text-bean'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {reviewSuccess && (
          <div className="mt-4">
            <SuccessNote message={reviewSuccess} />
          </div>
        )}
        {proposalsError && (
          <div className="mt-4">
            <ErrorNote message={proposalsError} />
          </div>
        )}
        {loadingProposals && (
          <div className="mt-4">
            <Spinner label="Loading applications" />
          </div>
        )}

        {!loadingProposals && !proposalsError && proposals.length === 0 && (
          <div className="mt-4">
            <EmptyState
              title={statusFilter ? 'No applications with this status' : 'No club applications yet'}
              hint={
                statusFilter
                  ? 'Try a different filter to see other applications.'
                  : 'Applications submitted through “Apply for club” will appear here.'
              }
            />
          </div>
        )}

        {!loadingProposals && proposals.length > 0 && (
          <p className="mt-4 text-[11px] uppercase tracking-wider text-olive font-medium">
            Showing {proposals.length} of {proposalsTotal} application{proposalsTotal === 1 ? '' : 's'}
          </p>
        )}

        <div className="mt-3 space-y-4">
          {proposals.map((proposal) => (
            <ProposalCard
              key={proposal.proposal_id}
              proposal={proposal}
              canReview={allowedReview}
              isFaculty={isFaculty}
              reviewing={reviewingId === proposal.proposal_id}
              reviewError={reviewErrors[proposal.proposal_id]}
              comment={comments[proposal.proposal_id] ?? ''}
              onCommentChange={(value) => setComment(proposal.proposal_id, value)}
              onReview={(decision) => void handleReview(proposal, decision)}
            />
          ))}
        </div>
      </section>

      {/* Branch breakdown */}
      {allowedAnalytics && overview && !loadingAnalytics && (
        <section className="mt-10">
          <h2 className="text-base font-bold text-bean">Branch breakdown</h2>
          <p className="mt-1 text-xs text-olive">
            Club, event, and registration activity grouped by master branch (e.g. B.Tech, M.Tech).
          </p>

          {overview.branch_metrics.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="No branches recorded" />
            </div>
          ) : (
            <div className="mt-4 overflow-x-auto rounded-2xl border border-rose/30 shadow-sm">
              <table className="w-full text-left text-sm">
                <thead className="bg-vanilla/20 text-xs uppercase tracking-wider text-olive">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Branch</th>
                    <th className="px-4 py-3 font-semibold">Active clubs</th>
                    <th className="px-4 py-3 font-semibold">Events hosted</th>
                    <th className="px-4 py-3 font-semibold">Registrations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rose/20">
                  {overview.branch_metrics.map((branch) => (
                    <tr key={branch.branch_id} className="bg-white hover:bg-vanilla/10 transition">
                      <td className="px-4 py-3 font-medium text-bean">{branch.branch_name}</td>
                      <td className="px-4 py-3 text-bean">{branch.active_clubs}</td>
                      <td className="px-4 py-3 text-bean">{branch.events_hosted}</td>
                      <td className="px-4 py-3 text-bean">{branch.total_registrations}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* Audit trail — Administrator only */}
      {allowedAudit && (
        <section className="mt-10">
          <h2 className="text-base font-bold text-bean">Recent audit activity</h2>
          <p className="mt-1 text-xs text-olive">
            Immutable record of sensitive operations — the last 25 entries.
          </p>

          <div className="mt-4 space-y-2">
            {loadingAudit && <Spinner label="Loading audit logs" />}
            {auditError && <ErrorNote message={auditError} />}
            {!loadingAudit && !auditError && auditLogs.length === 0 && (
              <EmptyState title="No audit entries yet" hint="Sensitive operations will appear here." />
            )}

            {auditLogs.map((log) => (
              <div
                key={log.audit_log_id}
                className="rounded-xl border border-rose/30 bg-white px-4 py-3 shadow-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-blood/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-blood">
                      {log.action}
                    </span>
                    <span className="text-xs text-olive">
                      {log.entity_type} #{log.entity_id}
                    </span>
                  </div>
                  <span className="text-xs text-olive">{formatDate(log.created_at)}</span>
                </div>
                <p className="mt-1.5 text-xs text-olive">
                  by <span className="font-medium text-bean">{log.actor_name ?? 'Unknown'}</span>
                  {log.actor_email && <span className="text-olive"> ({log.actor_email})</span>}
                </p>
                {log.details && (
                  <pre className="mt-2 overflow-x-auto rounded-lg bg-vanilla/20 px-3 py-2 text-[11px] leading-relaxed text-bean">
                    {log.details}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
