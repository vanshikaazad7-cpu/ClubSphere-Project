import { Link } from 'react-router-dom'
import { useClubs } from '../hooks/useClubs'
import { formatDate } from '../lib/format'
import ProgramSelector from '../components/ProgramSelector'
import { EmptyState, ErrorNote, PageHeader, Spinner, StatusBadge } from '../components/ui'

export default function ClubsPage() {
  const {
    clubs,
    search,
    setSearch,
    branchId,
    setBranchId,
    programId,
    setProgramId,
    loading,
    error,
  } = useClubs()

  return (
    <div>
      <PageHeader
        title="Clubs"
        icon="🏛️"
        subtitle="Browse every chartered student organisation at the university, along with its program, faculty manager and current membership."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search clubs by name or description…"
          className="w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20 sm:max-w-sm"
        />
        <div className="sm:w-96">
          <ProgramSelector
            branchId={branchId}
            programId={programId}
            onBranchChange={setBranchId}
            onProgramChange={setProgramId}
          />
        </div>
      </div>

      {error && <ErrorNote message={error} />}

      {loading ? (
        <Spinner label="Loading clubs" />
      ) : !error && clubs.length === 0 ? (
        <EmptyState
          title="No clubs found"
          hint="Try a different search term, or head to “Apply for club” to propose a new one."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {clubs.map((club) => (
            <article
              key={club.club_id}
              className="flex flex-col justify-between rounded-2xl border border-rose/30 bg-white p-5 transition hover:border-blood/40"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-bold text-bean">{club.name}</h2>
                  <StatusBadge status={club.status} />
                </div>

                <p className="mt-1 text-xs font-medium text-blood">
                  {club.program_name ?? 'Unassigned program'}
                </p>

                <p className="mt-3 text-sm leading-relaxed text-olive">
                  {club.description?.trim() || 'No description has been provided for this club yet.'}
                </p>

                <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-rose/30 pt-4 text-xs">
                  <div>
                    <dt className="text-olive">Members</dt>
                    <dd className="mt-0.5 text-base font-semibold text-bean">{club.member_count ?? 0}</dd>
                  </div>
                  <div>
                    <dt className="text-olive">Chartered</dt>
                    <dd className="mt-0.5 font-medium text-bean">{formatDate(club.created_at)}</dd>
                  </div>
                </dl>

                <p className="mt-3 text-xs text-olive">
                  Managed by <span className="font-medium text-bean">{club.manager_name ?? '—'}</span>
                </p>
              </div>

              <div className="mt-5 border-t border-rose/20 pt-4 flex items-center justify-between">
                <span className="text-[11px] text-olive uppercase tracking-wider font-medium">
                  {club.status}
                </span>
                <Link
                  to={`/joinclub?club_id=${club.club_id}`}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-rose/30 bg-vanilla/20 px-3 py-1.5 text-xs font-semibold text-bean transition hover:border-blood/40 hover:bg-blood hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
                >
                  Join club <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
