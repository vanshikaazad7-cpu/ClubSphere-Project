import { Link } from 'react-router-dom'

/**
 * 404 — displayed when navigating to any unknown URL.
 */
export default function NotFoundPage() {
  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-white px-4 py-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-blood/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-olive/10 blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-md text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-vanilla p-[1px] shadow-lg shadow-blood/20">
          <span className="flex h-full w-full items-center justify-center rounded-[15px] bg-white text-lg font-black text-blood">
            CS
          </span>
        </div>

        <p className="text-6xl font-black tracking-tight text-blood">404</p>

        <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-bean">
          Whoops! Wrong page. No clubs here
        </h1>

        <p className="mt-3 text-sm leading-relaxed text-olive">
          The address you followed does not match anything on ClubSphere. It may have been
          moved, or the link may have a typo.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/clubs"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-blood px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blood/20 transition hover:bg-blood/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
          >
            Browse clubs
          </Link>
          <Link
            to="/"
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-rose/30 bg-white px-6 py-2.5 text-sm font-semibold text-bean transition hover:border-blood/40 hover:text-blood focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
          >
            Home page
          </Link>
        </div>
      </div>
    </div>
  )
}
