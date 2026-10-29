import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Branch, Paginated } from '../lib/types'

/**
 * A cascading pair of dropdowns: first pick the master branch (e.g. "B.Tech"),
 * then the specialization (e.g. "B.Tech - AI/ML"). Selecting a different branch
 * resets the specialization to "choose one".
 */
export default function ProgramSelector({
  branchId,
  programId,
  onBranchChange,
  onProgramChange,
  required = false,
}: {
  branchId: string
  programId: string
  onBranchChange: (value: string) => void
  onProgramChange: (value: string) => void
  required?: boolean
}) {
  const [branches, setBranches] = useState<Branch[]>([])

  useEffect(() => {
    let cancelled = false
    api
      .get<Paginated<Branch>>('/branches')
      .then((res) => {
        if (!cancelled) setBranches(res.items)
      })
      .catch(() => {
        // The dropdowns are optional filters; fail silently if the API is unreachable.
      })
    return () => {
      cancelled = true
    }
  }, [])

  const selectedBranch = branches.find((b) => String(b.branch_id) === branchId)
  const programs = selectedBranch?.programs ?? []

  const selectClass =
    'w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20'

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div>
        <label htmlFor="branch" className="mb-1.5 block text-xs font-medium text-olive">
          Master program <span className="text-blood">*</span>
        </label>
        <select
          id="branch"
          value={branchId}
          onChange={(e) => {
            onBranchChange(e.target.value)
            // Reset the specialization when the master program changes.
            onProgramChange('')
          }}
          className={selectClass}
        >
          <option value="">Select a master program…</option>
          {branches.map((b) => (
            <option key={b.branch_id} value={b.branch_id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="program" className="mb-1.5 block text-xs font-medium text-olive">
          Specialization{' '}
          {required && <span className="text-blood">*</span>}
        </label>
        <select
          id="program"
          value={programId}
          onChange={(e) => onProgramChange(e.target.value)}
          disabled={!branchId}
          className={selectClass}
        >
          <option value="">
            {branchId ? 'Select a specialization…' : 'Choose a master program first'}
          </option>
          {programs.map((p) => (
            <option key={p.program_id} value={p.program_id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
