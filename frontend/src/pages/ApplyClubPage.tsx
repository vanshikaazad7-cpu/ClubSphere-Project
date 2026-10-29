import type { FormEvent } from 'react'
import { useProposals } from '../hooks/useProposals'
import { formatDate } from '../lib/format'
import { PROPOSAL_DESC_MIN } from '../domain/validation'
import ProgramSelector from '../components/ProgramSelector'
import {
  EmptyState,
  ErrorNote,
  PageHeader,
  Spinner,
  StatusBadge,
  SuccessNote,
} from '../components/ui'

export default function ApplyClubPage() {
  const {
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
  } = useProposals()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await submitProposal()
  }

  const inputClasses =
    'w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20'

  return (
    <div>
      <PageHeader
        title="Apply for club"
        icon="📝"
        subtitle="Propose a new student organisation. The proposal is reviewed in two stages — a Faculty Advisor recommendation, then final approval by the Head of Department, which charters the club automatically."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Submission form */}
        <section className="h-fit rounded-2xl border border-rose/30 bg-white p-6 shadow-sm">
          <h2 className="text-base font-bold text-bean">New club proposal</h2>
          <p className="mt-1 text-xs text-olive">
            Fields marked with an asterisk must be completed before submitting.
          </p>

          <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-4">
            <div>
              <label htmlFor="proposed-name" className="mb-1.5 block text-xs font-medium text-olive">
                Proposed club name <span className="text-blood">*</span>
              </label>
              <input
                id="proposed-name"
                type="text"
                required
                minLength={2}
                maxLength={150}
                value={proposedName}
                onChange={(e) => setProposedName(e.target.value)}
                placeholder="Robotics & Automation Society"
                className={inputClasses}
              />
            </div>

            <ProgramSelector
              branchId={branchId}
              programId={programId}
              onBranchChange={setBranchId}
              onProgramChange={setProgramId}
              required
            />

            <div>
              <label htmlFor="description" className="mb-1.5 block text-xs font-medium text-olive">
                Purpose &amp; activities <span className="text-blood">*</span>
              </label>
              <textarea
                id="description"
                required
                minLength={PROPOSAL_DESC_MIN}
                rows={6}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the club's mission, the activities it will run, and the students it aims to serve."
                className={`${inputClasses} resize-y`}
              />
              <p className="mt-1 text-right text-[11px] text-olive">
                {description.trim().length}/{PROPOSAL_DESC_MIN} characters minimum
              </p>
            </div>

            {success && <SuccessNote message={success} />}
            {error && <ErrorNote message={error} />}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-blood px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blood/20 transition hover:bg-blood/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              {submitting ? 'Submitting…' : 'Submit proposal'}
            </button>
          </form>
        </section>

        {/* Status of previously submitted proposals */}
        <section>
          <h2 className="text-base font-bold text-bean">Your proposals</h2>
          <p className="mt-1 text-xs text-olive">
            Approval history for every club you have proposed.
          </p>

          <div className="mt-5 space-y-4">
            {loadingProposals ? (
              <Spinner label="Loading proposals" />
            ) : proposals.length === 0 ? (
              <EmptyState
                title="No proposals yet"
                hint="Submit the form to start your first club proposal."
              />
            ) : (
              proposals.map((proposal) => (
                <article
                  key={proposal.proposal_id}
                  className="rounded-2xl border border-rose/30 bg-white p-5 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-bean">{proposal.proposed_name}</h3>
                      <p className="mt-0.5 text-xs text-olive">
                        {proposal.program_name ?? 'Unknown program'} • Submitted{' '}
                        {formatDate(proposal.submitted_at)}
                      </p>
                    </div>
                    <StatusBadge status={proposal.status} />
                  </div>

                  <p className="mt-3 text-xs leading-relaxed text-olive">{proposal.description}</p>

                  {proposal.approvals.length > 0 ? (
                    <ol className="mt-4 space-y-2 border-t border-rose/30 pt-4">
                      {proposal.approvals.map((approval) => (
                        <li key={approval.approval_id} className="text-xs">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold uppercase tracking-wide text-bean">
                              {approval.stage}
                            </span>
                            <StatusBadge status={approval.decision === 'approve' ? 'approved' : approval.decision} />
                            <span className="text-olive">
                              by {approval.reviewer_name ?? 'Reviewer'} on {formatDate(approval.decided_at)}
                            </span>
                          </div>
                          {approval.comment && (
                            <p className="mt-1 rounded-lg bg-vanilla/30 px-3 py-2 text-olive">
                              “{approval.comment}”
                            </p>
                          )}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="mt-4 border-t border-rose/30 pt-4 text-xs text-olive">
                      Awaiting first review by a Faculty Advisor.
                    </p>
                  )}
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
