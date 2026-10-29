import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import ClubsPage from './pages/ClubsPage'
import EventsPage from './pages/EventsPage'
import JoinClubPage from './pages/JoinClubPage'
import ApplyClubPage from './pages/ApplyClubPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import NotFoundPage from './pages/NotFoundPage'

// The cinematic landing page pulls in three.js — keep it code-split from the main app bundle.
const LandingPage = lazy(() => import('./pages/LandingPage'))

/** Redirects unauthenticated users to the login screen, preserving the intended URL. */
function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return children
}

/** Sends already-authenticated users away from the login screen. */
function RedirectIfAuthed({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) {
    return <Navigate to="/clubs" replace />
  }
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route
        path="/"
        element={
          <Suspense fallback={<div className="min-h-screen bg-white" />}>
            <LandingPage />
          </Suspense>
        }
      />

      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <LoginPage />
          </RedirectIfAuthed>
        }
      />

      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="clubs" element={<ClubsPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="joinclub" element={<JoinClubPage />} />
        <Route path="applyclub" element={<ApplyClubPage />} />
        <Route path="admin" element={<AdminDashboardPage />} />
      </Route>

      {/* 404 for any unmatched URLs */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
