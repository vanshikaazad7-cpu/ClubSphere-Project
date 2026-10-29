import { useSearchParams } from 'react-router-dom'
import { useJoinClub } from '../hooks/useJoinClub'
import { EmptyState, ErrorNote, PageHeader, Spinner, StatusBadge } from '../components/ui'

export default function JoinClubPage() {
  const [searchParams] = useSearchParams()
  const targetedClubId = searchParams.get('club_id')

  const {
    clubs,
    search,
    setSearch,
    loading,
    error,
    busyClubId,
    joinState,
    requestedClubIds,
    requestToJoin,
  } = useJoinClub(targetedClubId)

  return (
    <div>
      <PageHeader
        title="Join club"
        icon="🤝"
        subtitle="Send a membership request to any active club. Your request goes to the club manager, who approves or rejects it — you will be notified either way."
      />

      <div className="mb-6">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search active clubs…"
          className="w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20 sm:max-w-sm"
        />
      </div>

      {error && <ErrorNote message={error} />}

      {loading ? (
        <Spinner label="Loading clubs" />
      ) : !error && clubs.length === 0 ? (
        <EmptyState
          title="No active clubs available"
          hint="There are no clubs open for membership requests right now."
        />
      ) : (
        <div className="space-y-3">
          {clubs.map((club) => {
            const state = joinState[club.club_id]
            const isTargeted = targetedClubId && String(club.club_id) === targetedClubId
            const isRequested = requestedClubIds.has(club.club_id)

            return (
              <div
                key={club.club_id}
                className={`rounded-2xl border p-5 transition ${
                  isTargeted
                    ? 'border-blood bg-blood/5 shadow-md ring-1 ring-blood/30'
                    : 'border-rose/30 bg-white hover:border-blood/40'
                }`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-base font-bold text-bean">{club.name}</h2>
                      <StatusBadge status={club.status} />
                      {isTargeted && (
                        <span className="rounded-full bg-blood/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-blood">
                          Selected
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-olive">
                      {club.program_name ?? 'Unassigned program'} •{' '}
                      {club.member_count ?? 0} member{(club.member_count ?? 0) === 1 ? '' : 's'} • Managed by{' '}
                      <span className="font-medium text-bean">{club.manager_name ?? '—'}</span>
                    </p>
                    {club.description?.trim() && (
                      <p className="mt-2 line-clamp-2 text-sm text-olive">{club.description}</p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => void requestToJoin(club)}
                    disabled={busyClubId === club.club_id || isRequested}
                    className={`shrink-0 rounded-xl px-4 py-2 text-xs font-semibold shadow-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood disabled:cursor-not-allowed ${
                      isRequested
                        ? 'border border-olive/30 bg-olive/10 text-olive'
                        : 'bg-blood text-white shadow-blood/20 hover:bg-blood/90 cursor-pointer'
                    }`}
                  >
                    {busyClubId === club.club_id
                      ? 'Sending…'
                      : isRequested
                        ? '✓ Request sent'
                        : 'Request to join'}
                  </button>
                </div>

                {state && (
                  <p
                    className={`mt-3 text-xs font-medium ${
                      state.kind === 'error' ? 'text-blood' : 'text-olive'
                    }`}
                  >
                    {state.message}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
