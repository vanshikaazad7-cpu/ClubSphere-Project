# ClubSphere — Entity-Relationship (ER) Schema Specification

This document contains the complete database schema for **ClubSphere**, formatted for immediate visualization as an Entity-Relationship (ER) diagram in Mermaid, DBML, PlantUML, and SQL visualization tools.

---

## 1. Visual ER Diagram (Mermaid)

```mermaid
erDiagram
    %% Core Academic Hierarchy
    Branches ||--o{ Programs : "categorizes (1:N)"
    Programs ||--o{ Users : "enrolls (1:N)"
    Programs ||--o{ Clubs : "hosts (1:N)"
    Programs ||--o{ ClubProposals : "categorizes (1:N)"

    %% Identity & RBAC
    Roles ||--o{ Users : "assigns (1:N)"
    
    %% User Operational Relationships
    Users ||--o{ Clubs : "manages (1:N)"
    Users ||--o{ ClubMemberships : "joins (1:N)"
    Users ||--o{ Events : "creates (1:N)"
    Users ||--o{ EventRegistrations : "registers (1:N)"
    Users ||--o{ Attendance : "attends (1:N)"
    Users ||--o{ Attendance : "verifies (1:N)"
    Users ||--o{ EventOutcomes : "submits (1:N)"
    Users ||--o{ ClubProposals : "applies (1:N)"
    Users ||--o{ Approvals : "reviews (1:N)"
    Users ||--o{ Notifications : "receives (1:N)"
    Users ||--o{ AuditLogs : "acts (1:N)"
    Users ||--o{ UploadedFiles : "owns (1:N)"

    %% Club Operational Relationships
    Clubs ||--o{ ClubMemberships : "has members (1:N)"
    Clubs ||--o{ Events : "hosts (1:N)"

    %% Event Lifecycle
    Events ||--o{ EventRegistrations : "has RSVPs (1:N)"
    Events ||--o{ Attendance : "tracks check-ins (1:N)"
    Events ||--o| EventOutcomes : "concludes with (1:1)"

    %% Governance & Proposals
    ClubProposals ||--o{ Approvals : "evaluated through (1:N)"

    %% Entities
    Branches {
        int BranchId PK
        string BranchKey UK
        string Name UK
        string DegreeLevel
        int SortOrder
    }

    Programs {
        int ProgramId PK
        string ProgramKey UK
        int BranchId FK
        string Name
        string FullName
        string CollaborationPartner
        int SortOrder
    }

    Roles {
        int RoleId PK
        string RoleName UK
    }

    Users {
        int UserId PK
        string Email UK
        string PasswordHash
        string FullName
        int RoleId FK
        int ProgramId FK
        boolean IsActive
        int TokenVersion
        datetime CreatedAt
    }

    Clubs {
        int ClubId PK
        string Name UK
        int ProgramId FK
        int ManagerUserId FK
        string Description
        string Status
        datetime CreatedAt
    }

    ClubMemberships {
        int MembershipId PK
        int ClubId FK
        int UserId FK
        string Status
        string Role
        datetime JoinedAt
    }

    Events {
        int EventId PK
        int ClubId FK
        string Title
        string VenueText
        datetime EventDate
        datetime RegistrationDeadline
        int Capacity
        string Status
        int CreatedByUserId FK
    }

    EventRegistrations {
        int RegistrationId PK
        int EventId FK
        int UserId FK
        string Status
        datetime RegisteredAt
    }

    Attendance {
        int AttendanceId PK
        int EventId FK
        int UserId FK
        datetime CheckedInAt
        int RecordedByUserId FK
    }

    EventOutcomes {
        int OutcomeId PK
        int EventId FK_UK
        string Summary
        int AttendanceCountSnapshot
        int SubmittedByUserId FK
        datetime SubmittedAt
    }

    ClubProposals {
        int ProposalId PK
        int ApplicantUserId FK
        string ProposedName
        int ProgramId FK
        string Description
        string Status
        datetime SubmittedAt
    }

    Approvals {
        int ApprovalId PK
        int ProposalId FK
        int ReviewerUserId FK
        string Stage
        string Decision
        string Comment
        datetime DecidedAt
    }

    Notifications {
        int NotificationId PK
        int UserId FK
        string Type
        string Message
        boolean IsRead
        datetime CreatedAt
    }

    AuditLogs {
        int AuditLogId PK
        int ActorUserId FK
        string Action
        string EntityType
        int EntityId
        string Details
        datetime CreatedAt
    }

    UploadedFiles {
        string FileId PK
        int OwnerUserId FK
        string EntityType
        int EntityId
        string OriginalFilename
        string BlobPath
        string MimeType
        int FileSizeBytes
        datetime CreatedAt
    }
```

---

## 2. Relational Entity Dictionary

### 1. `Branches`
Master department / academic tracks (e.g. B.Tech, M.Tech, MBA).
* **BranchId** (`int`, PK, Auto-increment): Unique identifier.
* **BranchKey** (`varchar(50)`, Unique, Not Null): URL/JSON slug (e.g. `btech`).
* **Name** (`varchar(150)`, Unique, Not Null): Full qualification name.
* **DegreeLevel** (`varchar(50)`, Not Null): Degree tier (`undergraduate`, `postgraduate`, `doctoral`).
* **SortOrder** (`int`, Not Null, Default `0`): UI ordering rank.

### 2. `Programs`
Degree specializations under a branch (e.g. B.Tech in CSE with AI & ML).
* **ProgramId** (`int`, PK, Auto-increment): Unique identifier.
* **ProgramKey** (`varchar(100)`, Unique, Not Null): Specialization slug (e.g. `btech_cse_aiml`).
* **BranchId** (`int`, FK -> `Branches.BranchId`, Not Null): Parent branch.
* **Name** (`varchar(150)`, Not Null): Short display label.
* **FullName** (`varchar(255)`, Not Null): Full institutional description.
* **CollaborationPartner** (`varchar(150)`, Nullable): Industry co-partner (e.g. `Microsoft`, `IBM`).
* **SortOrder** (`int`, Not Null, Default `0`): UI display ordering rank.

### 3. `Roles`
Role-Based Access Control (RBAC) tiers.
* **RoleId** (`int`, PK, Auto-increment): Unique identifier.
* **RoleName** (`varchar(30)`, Unique, Not Null): Value enum: `Student`, `Club Manager`, `Faculty`, `HOD`, `Administrator`.

### 4. `Users`
Central identity, authentication, and session profile table.
* **UserId** (`int`, PK, Auto-increment): Unique identifier.
* **Email** (`varchar(256)`, Unique, Not Null): University email address.
* **PasswordHash** (`varchar(256)`, Not Null): BCrypt/Argon2 password hash.
* **FullName** (`varchar(150)`, Not Null): User's legal name.
* **RoleId** (`int`, FK -> `Roles.RoleId`, Not Null): System permission level.
* **ProgramId** (`int`, FK -> `Programs.ProgramId`, Nullable): Student or faculty department affiliation.
* **IsActive** (`boolean`, Not Null, Default `true`): Account standing status.
* **TokenVersion** (`int`, Not Null, Default `1`): Incremented on `/auth/logout` to instantly revoke all active JWT tokens.
* **CreatedAt** (`datetime`, Not Null): Registration timestamp in UTC.

### 5. `Clubs`
Chartered university student organizations.
* **ClubId** (`int`, PK, Auto-increment): Unique identifier.
* **Name** (`varchar(150)`, Unique, Not Null): Official club title.
* **ProgramId** (`int`, FK -> `Programs.ProgramId`, Not Null): Host academic program.
* **ManagerUserId** (`int`, FK -> `Users.UserId`, Not Null): Designated lead student or faculty manager.
* **Description** (`text`, Nullable): Mission statement and charter details.
* **Status** (`varchar(20)`, Not Null, Default `pending`): Constraint: `pending`, `active`, `suspended`.
* **CreatedAt** (`datetime`, Not Null): Charter date in UTC.

### 6. `ClubMemberships`
Student rosters and membership requests.
* **MembershipId** (`int`, PK, Auto-increment): Unique identifier.
* **ClubId** (`int`, FK -> `Clubs.ClubId` ON DELETE CASCADE, Not Null): Target club.
* **UserId** (`int`, FK -> `Users.UserId`, Not Null): Member student.
* **Status** (`varchar(20)`, Not Null, Default `requested`): Constraint: `requested`, `active`, `removed`.
* **Role** (`varchar(30)`, Not Null, Default `Member`): `Member` or `Lead`.
* **JoinedAt** (`datetime`, Not Null): Request or admission timestamp.
* *Constraints*: Unique tuple `(ClubId, UserId)`.

### 7. `Events`
Campus activities and club events with live seat caps.
* **EventId** (`int`, PK, Auto-increment): Unique identifier.
* **ClubId** (`int`, FK -> `Clubs.ClubId` ON DELETE CASCADE, Not Null): Host club.
* **Title** (`varchar(200)`, Not Null): Event title.
* **VenueText** (`varchar(200)`, Nullable): Room number, auditorium, or virtual link.
* **EventDate** (`datetime`, Not Null): Scheduled start time (UTC).
* **RegistrationDeadline** (`datetime`, Not Null): Cutoff time (must be `<= EventDate`).
* **Capacity** (`int`, Not Null): Maximum registrant threshold (`Capacity > 0`).
* **Status** (`varchar(20)`, Not Null, Default `draft`): `draft`, `published`, `completed`, `cancelled`.
* **CreatedByUserId** (`int`, FK -> `Users.UserId`, Not Null): Event organizer.

### 8. `EventRegistrations`
Student RSVPs and seat allocation.
* **RegistrationId** (`int`, PK, Auto-increment): Unique identifier.
* **EventId** (`int`, FK -> `Events.EventId` ON DELETE CASCADE, Not Null): Target event.
* **UserId** (`int`, FK -> `Users.UserId`, Not Null): Registrant.
* **Status** (`varchar(20)`, Not Null, Default `confirmed`): `confirmed`, `waitlisted`, `cancelled`.
* **RegisteredAt** (`datetime`, Not Null): Registration timestamp.
* *Constraints*: Unique tuple `(EventId, UserId)`.

### 9. `Attendance`
Verified event attendance check-ins.
* **AttendanceId** (`int`, PK, Auto-increment): Unique identifier.
* **EventId** (`int`, FK -> `Events.EventId` ON DELETE CASCADE, Not Null): Event attended.
* **UserId** (`int`, FK -> `Users.UserId`, Not Null): Attending student.
* **CheckedInAt** (`datetime`, Not Null): Check-in verification timestamp.
* **RecordedByUserId** (`int`, FK -> `Users.UserId`, Not Null): Manager or faculty member validating entry.
* *Constraints*: Unique tuple `(EventId, UserId)`.

### 10. `EventOutcomes`
Post-event summary, analytics snapshot, and retrospective.
* **OutcomeId** (`int`, PK, Auto-increment): Unique identifier.
* **EventId** (`int`, FK -> `Events.EventId` ON DELETE CASCADE, Unique, Not Null): 1-to-1 relationship with `Events`.
* **Summary** (`text`, Nullable): Qualitative report and KPI summary.
* **AttendanceCountSnapshot** (`int`, Not Null, Default `0`): Frozen headcount of confirmed attendees.
* **SubmittedByUserId** (`int`, FK -> `Users.UserId`, Not Null): Manager submitting report.
* **SubmittedAt** (`datetime`, Not Null): Submission timestamp.

### 11. `ClubProposals`
Student applications to charter new clubs.
* **ProposalId** (`int`, PK, Auto-increment): Unique identifier.
* **ApplicantUserId** (`int`, FK -> `Users.UserId`, Not Null): Proposing student.
* **ProposedName** (`varchar(150)`, Not Null): Requested club title.
* **ProgramId** (`int`, FK -> `Programs.ProgramId`, Not Null): Target academic program.
* **Description** (`text`, Not Null): Charter proposal (mission, activities, goals).
* **Status** (`varchar(20)`, Not Null, Default `submitted`): `submitted`, `changes_requested`, `approved`, `rejected`.
* **SubmittedAt** (`datetime`, Not Null): Initial application timestamp.

### 12. `Approvals`
Two-stage governance review trail (Faculty -> HOD).
* **ApprovalId** (`int`, PK, Auto-increment): Unique identifier.
* **ProposalId** (`int`, FK -> `ClubProposals.ProposalId` ON DELETE CASCADE, Not Null): Target proposal.
* **ReviewerUserId** (`int`, FK -> `Users.UserId`, Not Null): Reviewing Faculty, HOD, or Administrator.
* **Stage** (`varchar(20)`, Not Null): `faculty` (recommendation) or `hod` (final approval).
* **Decision** (`varchar(20)`, Not Null): `approve`, `reject`, `changes_requested`.
* **Comment** (`text`, Nullable): Mandatory reasoning when rejecting or requesting revisions.
* **DecidedAt** (`datetime`, Not Null): Timestamp of the review decision.

### 13. `Notifications`
In-app user notifications for events, proposals, and memberships.
* **NotificationId** (`int`, PK, Auto-increment): Unique identifier.
* **UserId** (`int`, FK -> `Users.UserId`, Not Null): Recipient user.
* **Type** (`varchar(50)`, Not Null): Category code (e.g. `REGISTRATION_CONFIRMATION`, `PROPOSAL_REVIEW`).
* **Message** (`varchar(500)`, Not Null): User-facing alert text.
* **IsRead** (`boolean`, Not Null, Default `false`): Read status indicator.
* **CreatedAt** (`datetime`, Not Null): Generation timestamp.

### 14. `AuditLogs`
Immutable security and compliance audit trail.
* **AuditLogId** (`int`, PK, Auto-increment): Unique identifier.
* **ActorUserId** (`int`, FK -> `Users.UserId`, Not Null): Performing user.
* **Action** (`varchar(100)`, Not Null): Action code (e.g. `CLUB_UPDATED`, `PROPOSAL_APPROVED`).
* **EntityType** (`varchar(50)`, Not Null): Target table (e.g. `Clubs`, `Events`).
* **EntityId** (`int`, Not Null): Target entity primary key ID.
* **Details** (`text`, Nullable): JSON payload snapshot of change delta.
* **CreatedAt** (`datetime`, Not Null): Event timestamp.

### 15. `UploadedFiles`
Uploaded attachments, banners, and proposal documentation.
* **FileId** (`varchar(64)`, PK): SHA-256 / UUID alphanumeric identifier.
* **OwnerUserId** (`int`, FK -> `Users.UserId`, Not Null): Uploader.
* **EntityType** (`varchar(50)`, Not Null): Attached entity table.
* **EntityId** (`int`, Not Null): Attached entity ID.
* **OriginalFilename** (`varchar(255)`, Not Null): Original client file name.
* **BlobPath** (`varchar(500)`, Not Null): Internal storage path / Azure Blob URI.
* **MimeType** (`varchar(100)`, Not Null): Verified MIME type (`image/png`, `application/pdf`, etc.).
* **FileSizeBytes** (`int`, Not Null): File size in bytes.
* **CreatedAt** (`datetime`, Not Null): Upload timestamp.

---

## 3. How to Render the Diagram

1. **Mermaid Live Editor**:
   - Open [mermaid.live](https://mermaid.live).
   - Copy the Mermaid block from Section 1 above or use [schema.mermaid](file:///d:/e/docs/schema.mermaid).
   - Paste into the editor to view, zoom, and export SVG/PNG.
2. **dbdiagram.io**:
   - Open [dbdiagram.io](https://dbdiagram.io).
   - Open the exported [schema.dbml](file:///d:/e/docs/schema.dbml) file.
   - Paste the DBML content to edit relationships and generate PDF/image exports interactively.
3. **VS Code / Markdown Preview**:
   - Install the **Markdown Preview Mermaid Support** extension to preview the diagram inside your IDE.
