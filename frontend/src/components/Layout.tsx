import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { NAV_ITEMS, ROLE_LABELS } from '../domain/constants'
import { canAccessAdmin } from '../domain/permissions'
import NotificationsPopover from './NotificationsPopover'

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const [menuOpen, setMenuOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const sidebarRef = useRef<HTMLElement>(null)

  const initials = (user?.full_name ?? '?')
    .split(' ')
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()

  // Manage modal accessibility, scroll lock, keyboard trap, and Escape key
  useEffect(() => {
    if (!menuOpen) return

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
        menuButtonRef.current?.focus()
        return
      }
      if (event.key !== 'Tab') return

      const focusable = sidebarRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled])',
      )
      if (!focusable || focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [menuOpen])

  function closeMenu() {
    setMenuOpen(false)
    menuButtonRef.current?.focus()
  }

  async function handleLogout() {
    setMenuOpen(false)
    await logout()
    navigate('/login', { replace: true })
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-11 w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood ${
      isActive
        ? 'bg-blood text-white shadow-lg shadow-blood/20'
        : 'text-olive hover:bg-vanilla/40 hover:text-bean'
    }`

  const brand = (
    <div className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-vanilla p-[1px] shadow-sm">
        <div className="flex h-full w-full items-center justify-center rounded-[11px] bg-white text-sm font-black text-blood">
          CS
        </div>
      </div>
      <span className="text-lg font-bold text-blood">ClubSphere</span>
    </div>
  )

  return (
    <div className="flex min-h-dvh flex-col bg-white text-bean lg:flex-row">
      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex min-h-14 items-center justify-between border-b border-rose/30 bg-white/95 px-3 pt-[env(safe-area-inset-top)] backdrop-blur lg:hidden">
        <div className="flex items-center gap-2">
          <button
            ref={menuButtonRef}
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label="Open navigation menu"
            aria-expanded={menuOpen}
            aria-controls="app-sidebar"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-rose/30 text-bean transition hover:border-blood/40 hover:text-blood focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-5 w-5" aria-hidden="true">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
          {brand}
        </div>

        <div className="flex items-center gap-2">
          <NotificationsPopover isAuthenticated={isAuthenticated} />
        </div>
      </header>

      {/* Scrim: dims background content on mobile */}
      <div
        onClick={closeMenu}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-bean/60 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${
          menuOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />

      {/* Sidebar / off-canvas drawer */}
      <aside
        id="app-sidebar"
        ref={sidebarRef}
        aria-label="Primary navigation"
        aria-modal={menuOpen ? 'true' : undefined}
        className={`fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-rose/30 bg-white backdrop-blur transition-[transform,visibility] duration-300 ease-out lg:sticky lg:top-0 lg:z-auto lg:h-dvh lg:w-64 lg:max-w-none lg:translate-x-0 lg:visible ${
          menuOpen ? 'visible translate-x-0' : 'invisible -translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-rose/30 px-5 pt-[env(safe-area-inset-top)]">
          {brand}
          <button
            ref={closeButtonRef}
            type="button"
            onClick={closeMenu}
            aria-label="Close navigation menu"
            className="flex h-10 w-10 items-center justify-center rounded-xl text-olive transition hover:bg-vanilla/40 hover:text-bean focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer lg:hidden"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="h-5 w-5" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMenuOpen(false)}
              className={linkClass}
            >
              <span aria-hidden className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}

          {canAccessAdmin(user) && (
            <>
              <div className="my-3 border-t border-rose/30" />
              <NavLink
                to="/admin"
                onClick={() => setMenuOpen(false)}
                className={linkClass}
              >
                <span aria-hidden className="text-base">🛡️</span>
                Admin Dashboard
              </NavLink>
            </>
          )}
        </nav>

        {/* Profile and sign out footer */}
        <div className="border-t border-rose/30 p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-vanilla text-xs font-bold text-bean">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-bean">{user?.full_name}</p>
                <p className="truncate text-xs text-olive">
                  {ROLE_LABELS[user?.role ?? ''] ?? user?.role}
                </p>
              </div>
            </div>
            <div className="hidden lg:block">
              <NotificationsPopover isAuthenticated={isAuthenticated} />
            </div>
          </div>
          <button
            type="button"
            onClick={() => void handleLogout()}
            className="mt-3 min-h-11 w-full rounded-lg border border-rose/30 bg-white px-3 py-2 text-xs font-medium text-bean transition hover:border-blood/40 hover:text-blood focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Routed page content */}
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1 overflow-x-hidden">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
