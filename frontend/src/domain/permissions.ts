import { ADMIN_OR_HOD_ROLES, AUDIT_ROLES, REVIEW_ROLES } from './constants'
import type { SessionProfile } from './types'

export function canAccessAdmin(user: SessionProfile | null): boolean {
  if (!user) return false
  return REVIEW_ROLES.has(user.role)
}

export function canViewAnalytics(user: SessionProfile | null): boolean {
  if (!user) return false
  return ADMIN_OR_HOD_ROLES.has(user.role)
}

export function canViewAuditLogs(user: SessionProfile | null): boolean {
  if (!user) return false
  return AUDIT_ROLES.has(user.role)
}

export function canReviewProposals(user: SessionProfile | null): boolean {
  if (!user) return false
  return REVIEW_ROLES.has(user.role)
}

export function isFacultyReviewer(user: SessionProfile | null): boolean {
  return user?.role === 'Faculty'
}

export function isHODOrAdmin(user: SessionProfile | null): boolean {
  if (!user) return false
  return ADMIN_OR_HOD_ROLES.has(user.role)
}
