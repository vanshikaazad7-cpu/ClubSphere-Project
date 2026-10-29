export const PROPOSAL_NAME_MIN = 2
export const PROPOSAL_NAME_MAX = 150
export const PROPOSAL_DESC_MIN = 10
export const PASSWORD_MIN_LENGTH = 8

export function validateProposalInput(name: string, programId: string, description: string): string | null {
  const trimmedName = name.trim()
  if (!trimmedName || trimmedName.length < PROPOSAL_NAME_MIN) {
    return `Proposed club name must be at least ${PROPOSAL_NAME_MIN} characters.`
  }
  if (trimmedName.length > PROPOSAL_NAME_MAX) {
    return `Proposed club name cannot exceed ${PROPOSAL_NAME_MAX} characters.`
  }
  if (!programId) {
    return 'Please select the program your club will belong to.'
  }
  if (description.trim().length < PROPOSAL_DESC_MIN) {
    return `Please provide a description of at least ${PROPOSAL_DESC_MIN} characters.`
  }
  return null
}

export function validateRegistrationInput(fullName: string, email: string, password: string): string | null {
  if (fullName.trim().length < 2) {
    return 'Please enter your full name (minimum 2 characters).'
  }
  if (!email.includes('@') || !email.includes('.')) {
    return 'Please enter a valid university email address.'
  }
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters long.`
  }
  return null
}

export function validateReviewDecision(decision: 'approve' | 'reject' | 'changes_requested', comment: string): string | null {
  if (decision !== 'approve' && !comment.trim()) {
    return 'A non-empty comment is required when rejecting or requesting changes.'
  }
  return null
}
