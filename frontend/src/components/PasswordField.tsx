import { useState } from 'react'

interface PasswordFieldProps {
  id?: string
  name?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
  required?: boolean
  minLength?: number
  className?: string
  label?: string
  autoComplete?: string
}

export default function PasswordField({
  id = 'password',
  name = 'password',
  value,
  onChange,
  placeholder = '••••••••',
  required = false,
  minLength,
  className = '',
  label = 'Password',
  autoComplete = 'current-password',
}: PasswordFieldProps) {
  const [showPassword, setShowPassword] = useState(false)

  const defaultInputClass =
    'w-full rounded-xl border border-rose/30 bg-white min-h-11 pl-4 pr-11 py-2.5 text-sm text-bean placeholder-rose outline-none transition focus:border-blood focus:ring-2 focus:ring-blood/20'

  return (
    <div>
      {label && (
        <label htmlFor={id} className="mb-1.5 block text-xs font-medium text-olive">
          {label} {required && <span className="text-blood">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          id={id}
          name={name}
          type={showPassword ? 'text' : 'password'}
          required={required}
          minLength={minLength}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={className || defaultInputClass}
        />
        <button
          type="button"
          onClick={() => setShowPassword((prev) => !prev)}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
          className="absolute inset-y-0 right-0 flex h-11 w-11 items-center justify-center text-olive transition hover:text-bean focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blood cursor-pointer"
        >
          {showPassword ? (
            // Eye off icon
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          ) : (
            // Eye icon
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}
