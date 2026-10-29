// Domain models and data transfer contracts mirroring backend schemas

export interface SessionProfile {
  user_id: number
  full_name: string
  email: string
  role: string
  program_id?: number | null
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  role: string
  user_id: number
  full_name: string
  email: string
}

export interface UserResponse {
  user_id: number
  email: string
  full_name: string
  role: string
  program_id?: number | null
  program_name?: string | null
  branch_id?: number | null
  branch_name?: string | null
  is_active: boolean
  created_at: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface Club {
  club_id: number
  name: string
  program_id: number
  program_name?: string | null
  branch_id?: number | null
  branch_name?: string | null
  manager_user_id: number
  manager_name?: string | null
  description?: string | null
  status: string
  created_at: string
  member_count?: number
}

export interface ClubMembership {
  membership_id: number
  club_id: number
  user_id: number
  user_name?: string | null
  user_email?: string | null
  role?: string
  status: string
  joined_at: string
}

export interface MembershipJoinResponse {
  membership_id: number
  club_id: number
  user_id: number
  status: string
  joined_at: string
}

export interface EventItem {
  event_id: number
  club_id: number
  club_name?: string | null
  title: string
  venue_text?: string | null
  event_date: string
  registration_deadline: string
  capacity: number
  status: string
  created_by_user_id: number
  confirmed_registrations: number
  seats_left: number
}

export interface RegistrationResponse {
  registration_id: number
  event_id: number
  user_id: number
  status: string
  registered_at: string
}

export interface Approval {
  approval_id: number
  proposal_id: number
  reviewer_user_id: number
  reviewer_name?: string | null
  stage: string
  decision: string
  comment?: string | null
  decided_at: string
}

export interface Proposal {
  proposal_id: number
  applicant_user_id: number
  applicant_name?: string | null
  proposed_name: string
  program_id: number
  program_name?: string | null
  branch_id?: number | null
  branch_name?: string | null
  description: string
  status: string
  submitted_at: string
  approvals: Approval[]
  created_club_id?: number | null
}

export interface Program {
  program_id: number
  program_key: string
  name: string
  full_name: string
  collaboration_partner?: string | null
  sort_order: number
}

export interface Branch {
  branch_id: number
  branch_key: string
  name: string
  degree_level: string
  sort_order: number
  programs: Program[]
}

export interface BranchMetric {
  branch_id: number
  branch_name: string
  active_clubs: number
  events_hosted: number
  total_registrations: number
}

export interface AnalyticsOverview {
  total_clubs: number
  active_clubs: number
  pending_proposals: number
  total_events: number
  published_events: number
  total_registrations: number
  confirmed_registrations: number
  total_attendance: number
  avg_attendance_rate: number
  total_students: number
  branch_metrics: BranchMetric[]
}

export interface AuditLog {
  audit_log_id: number
  actor_user_id: number
  actor_email?: string | null
  actor_name?: string | null
  action: string
  entity_type: string
  entity_id: number
  details?: string | null
  created_at: string
}

export interface InAppNotification {
  notification_id: number
  user_id: number
  type: string
  message: string
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  items: InAppNotification[]
  total: number
  unread_count: number
}

export interface LastUpdatedMetadata {
  last_updated: string | null
  last_updated_source: string | null
  last_club_created_at: string | null
  last_user_created_at: string | null
  latest_event_date: string | null
  counts: {
    clubs: number
    events: number
    registrations: number
    students: number
  }
  generated_at: string | null
}
