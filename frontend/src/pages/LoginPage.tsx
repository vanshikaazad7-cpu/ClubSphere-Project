import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ProgramSelector from '../components/ProgramSelector'
import PasswordField from '../components/PasswordField'
import { ErrorNote } from '../components/ui'
import { validateRegistrationInput } from '../domain/validation'

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Where the user was headed before being redirected to login
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/clubs'
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [branchId, setBranchId] = useState('')
  const [programId, setProgramId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const isRegister = mode === 'register'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (isRegister) {
      const validationError = validateRegistrationInput(fullName, email, password)
      if (validationError) {
        setError(validationError)
        return
      }
    }

    setLoading(true)
    try {
      if (isRegister) {
        await register({
          full_name: fullName.trim(),
          email: email.trim(),
          password,
          program_id: programId ? Number(programId) : undefined,
        })
        // Switch to login tab on success
        setMode('login')
        setPassword('')
      } else {
        await login(email.trim(), password)
        navigate(redirectTo, { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const inputClasses =
    'w-full rounded-xl border border-rose/30 bg-white min-h-11 px-4 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20'

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-white px-4 py-10 pt-[max(2.5rem,env(safe-area-inset-top))] pb-[max(2.5rem,env(safe-area-inset-bottom))]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-blood/10 blur-3xl" />
        <div className="absolute top-1/3 -right-32 h-96 w-96 rounded-full bg-olive/10 blur-3xl" />
        <div className="absolute -bottom-32 left-1/3 h-96 w-96 rounded-full bg-blood/10 blur-3xl" />
      </div>

      <Link
        to="/"
        className="absolute top-5 left-5 z-10 text-sm font-medium text-olive transition hover:text-bean"
      >
        ← ClubSphere home
      </Link>

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-vanilla p-[1px] shadow-lg shadow-blood/20">
            <span className="text-lg font-black text-blood">CS</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-bean">ClubSphere</h1>
          <p className="mt-2 text-sm text-olive">
            University Club &amp; Activity Lifecycle Management Platform
          </p>
        </div>

        <div className="rounded-2xl border border-rose/30 bg-white p-6 shadow-xl backdrop-blur sm:p-8">
          <div className="mb-6 grid grid-cols-2 gap-1 rounded-xl border border-rose/20 bg-vanilla/30 p-1">
            {(['login', 'register'] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => {
                  setMode(tab)
                  setError(null)
                }}
                className={`min-h-11 rounded-lg px-3 py-2 text-sm font-medium transition cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood ${
                  mode === tab ? 'bg-blood text-white shadow' : 'text-olive hover:text-bean'
                }`}
              >
                {tab === 'login' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            {isRegister && (
              <div>
                <label htmlFor="full-name" className="mb-1.5 block text-xs font-medium text-olive">
                  Full name <span className="text-blood">*</span>
                </label>
                <input
                  id="full-name"
                  type="text"
                  required
                  minLength={2}
                  maxLength={150}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Aryan Chatterjee"
                  className={inputClasses}
                />
              </div>
            )}

            {isRegister && (
              <ProgramSelector
                branchId={branchId}
                programId={programId}
                onBranchChange={setBranchId}
                onProgramChange={setProgramId}
              />
            )}

            <div>
              <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-olive">
                University email <span className="text-blood">*</span>
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
                className={inputClasses}
              />
            </div>

            <PasswordField
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isRegister ? 8 : undefined}
              placeholder={isRegister ? 'Minimum 8 characters' : '••••••••'}
            />

            {error && <ErrorNote message={error} />}

            <button
              type="submit"
              disabled={loading}
              className="min-h-11 w-full rounded-xl bg-blood px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blood/20 transition hover:bg-blood/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood disabled:cursor-not-allowed disabled:opacity-60 cursor-pointer"
            >
              {loading ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs leading-relaxed text-olive">
            New accounts start as <span className="font-semibold text-bean">Student</span>. Roles such as Club
            Manager, Faculty Advisor, HOD and Administrator are assigned by an administrator.
          </p>
        </div>
      </div>
    </div>
  )
}
