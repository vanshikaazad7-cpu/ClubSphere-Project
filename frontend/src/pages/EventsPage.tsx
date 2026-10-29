import { useEvents } from '../hooks/useEvents'
import { formatDate } from '../lib/format'
import { EmptyState, ErrorNote, PageHeader, Spinner, StatusBadge } from '../components/ui'

export default function EventsPage() {
  const {
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
  } = useEvents()

  return (
    <div>
      <PageHeader
        title="Events"
        icon="📅"
        subtitle="Every published club event with live seat availability. Register while seats remain and before the registration deadline."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search events by title or venue…"
          className="w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20 sm:max-w-sm"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20 sm:w-56"
        >
          <option value="published">Published</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="draft">Draft</option>
        </select>
      </div>

      {error && <ErrorNote message={error} />}

      {loading ? (
        <Spinner label="Loading events" />
      ) : !error && events.length === 0 ? (
        <EmptyState title="No events found" hint="There are no events matching the current filters." />
      ) : (
        <div className="space-y-4">
          {events.map((event) => {
            const filled = event.capacity > 0 ? (event.confirmed_registrations / event.capacity) * 100 : 0
            const isFull = event.seats_left <= 0
            const isRegistered = registeredIds.has(event.event_id)
            const note = feedback[event.event_id]

            return (
              <article
                key={event.event_id}
                className="rounded-2xl border border-rose/30 bg-white p-5 transition hover:border-blood/40"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-lg font-bold text-bean">{event.title}</h2>
                      <StatusBadge status={event.status} />
                      {isRegistered && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-olive/30 bg-olive/10 px-2.5 py-0.5 text-[11px] font-semibold text-olive">
                          ✓ You are registered
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs font-medium text-blood">
                      Hosted by {event.club_name ?? 'a university club'}
                    </p>

                    <dl className="mt-3 grid grid-cols-1 gap-x-8 gap-y-1 text-xs sm:grid-cols-2">
                      <div className="flex gap-2">
                        <dt className="text-olive">Venue:</dt>
                        <dd className="text-bean">{event.venue_text || 'To be announced'}</dd>
                      </div>
                      <div className="flex gap-2">
                        <dt className="text-olive">Starts:</dt>
                        <dd className="text-bean">{formatDate(event.event_date)}</dd>
                      </div>
                      <div className="flex gap-2">
                        <dt className="text-olive">Register by:</dt>
                        <dd className="text-bean">{formatDate(event.registration_deadline)}</dd>
                      </div>
                    </dl>
                  </div>

                  <div className="shrink-0 sm:text-right">
                    <p className={`text-2xl font-extrabold ${isFull && !isRegistered ? 'text-blood' : 'text-bean'}`}>
                      {event.seats_left}
                    </p>
                    <p className="text-xs text-olive">of {event.capacity} seats left</p>
                    <button
                      type="button"
                      onClick={() => void toggleRegistration(event)}
                      disabled={
                        busyEventId === event.event_id ||
                        event.status !== 'published' ||
                        (!isRegistered && isFull)
                      }
                      className={`mt-3 min-h-10 rounded-xl px-4 py-2 text-xs font-semibold shadow-sm transition disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-olive cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood ${
                        isRegistered
                          ? 'border border-rose/30 bg-white text-blood hover:bg-blood/10'
                          : 'bg-blood text-white shadow-blood/20 hover:bg-blood/90'
                      }`}
                    >
                      {busyEventId === event.event_id
                        ? 'Working…'
                        : isRegistered
                          ? 'Cancel registration'
                          : isFull
                            ? 'Event full'
                            : 'Register'}
                    </button>
                  </div>
                </div>

                <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-vanilla/40">
                  <div
                    className={`h-full rounded-full transition-all ${isFull ? 'bg-blood' : 'bg-olive'}`}
                    style={{ width: `${Math.min(100, filled)}%` }}
                  />
                </div>

                {note && (
                  <p
                    className={`mt-3 text-xs font-medium ${note.kind === 'error' ? 'text-blood' : 'text-olive'}`}
                  >
                    {note.message}
                  </p>
                )}
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
