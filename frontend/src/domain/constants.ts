// Application and domain constants

export const ROLE_LABELS: Record<string, string> = {
  Student: 'Student',
  'Club Manager': 'Club Manager',
  Faculty: 'Faculty Advisor',
  HOD: 'Head of Department',
  Administrator: 'Administrator',
}

export const ADMIN_OR_HOD_ROLES = new Set(['Administrator', 'HOD'])
export const REVIEW_ROLES = new Set(['Administrator', 'HOD', 'Faculty'])
export const AUDIT_ROLES = new Set(['Administrator'])

export const NAV_ITEMS = [
  { to: '/clubs', label: 'Clubs', icon: '🏛️' },
  { to: '/events', label: 'Events', icon: '📅' },
  { to: '/joinclub', label: 'Join club', icon: '🤝' },
  { to: '/applyclub', label: 'Apply for club', icon: '📝' },
] as const

export const PROPOSAL_STATUS_TABS = [
  { key: '', label: 'All' },
  { key: 'submitted', label: 'Submitted' },
  { key: 'changes_requested', label: 'Changes requested' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
] as const

export const BADGE_STYLES: Record<string, string> = {
  active: 'bg-olive/10 text-olive border-olive/30',
  published: 'bg-olive/10 text-olive border-olive/30',
  approved: 'bg-olive/10 text-olive border-olive/30',
  confirmed: 'bg-olive/10 text-olive border-olive/30',
  requested: 'bg-rose/10 text-rose border-rose/30',
  submitted: 'bg-rose/10 text-rose border-rose/30',
  pending: 'bg-rose/10 text-rose border-rose/30',
  draft: 'bg-rose/10 text-bean border-rose/30',
  completed: 'bg-blood/10 text-blood border-blood/30',
  changes_requested: 'bg-rose/10 text-rose border-rose/30',
  cancelled: 'bg-rose/10 text-olive border-rose/30',
  removed: 'bg-blood/10 text-blood border-blood/30',
  rejected: 'bg-blood/10 text-blood border-blood/30',
  suspended: 'bg-blood/10 text-blood border-blood/30',
}
