-- ==============================================================================
-- ClubSphere — Azure SQL Database DDL Schema
-- System Design Document (SDD) Section 3.5 Implementation
-- ==============================================================================

-- 1. Departments Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Departments')
BEGIN
    CREATE TABLE Departments (
        DepartmentId INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(150) NOT NULL UNIQUE,
        Code NVARCHAR(20) NOT NULL UNIQUE
    );
END;

-- 2. Roles Lookup Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Roles')
BEGIN
    CREATE TABLE Roles (
        RoleId INT IDENTITY(1,1) PRIMARY KEY,
        RoleName NVARCHAR(30) NOT NULL UNIQUE
        -- Seeded: Student, Club Manager, Faculty, HOD, Administrator
    );
END;

-- 3. Users Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
BEGIN
    CREATE TABLE Users (
        UserId INT IDENTITY(1,1) PRIMARY KEY,
        Email NVARCHAR(256) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(256) NOT NULL,
        FullName NVARCHAR(150) NOT NULL,
        RoleId INT NOT NULL REFERENCES Roles(RoleId),
        DepartmentId INT NULL REFERENCES Departments(DepartmentId),
        IsActive BIT NOT NULL DEFAULT 1,
        TokenVersion INT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Users_Email ON Users(Email);
END;

-- 4. Clubs Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Clubs')
BEGIN
    CREATE TABLE Clubs (
        ClubId INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(150) NOT NULL UNIQUE,
        DepartmentId INT NOT NULL REFERENCES Departments(DepartmentId),
        ManagerUserId INT NOT NULL REFERENCES Users(UserId),
        Description NVARCHAR(MAX) NULL,
        Status NVARCHAR(20) NOT NULL DEFAULT 'pending'
            CONSTRAINT CK_Clubs_Status CHECK (Status IN ('pending', 'active', 'suspended')),
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Clubs_Dept_Status ON Clubs(DepartmentId, Status);
END;

-- 5. Club Memberships Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ClubMemberships')
BEGIN
    CREATE TABLE ClubMemberships (
        MembershipId INT IDENTITY(1,1) PRIMARY KEY,
        ClubId INT NOT NULL REFERENCES Clubs(ClubId) ON DELETE CASCADE,
        UserId INT NOT NULL REFERENCES Users(UserId),
        Status NVARCHAR(20) NOT NULL DEFAULT 'requested'
            CONSTRAINT CK_ClubMemberships_Status CHECK (Status IN ('requested', 'active', 'removed')),
        Role NVARCHAR(30) NOT NULL DEFAULT 'Member'
            CONSTRAINT CK_ClubMemberships_Role CHECK (Role IN ('Member', 'Lead')),
        JoinedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_Club_User UNIQUE (ClubId, UserId)
    );
    CREATE INDEX IX_ClubMemberships_User ON ClubMemberships(UserId, Status);
END;

-- 6. Events Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Events')
BEGIN
    CREATE TABLE Events (
        EventId INT IDENTITY(1,1) PRIMARY KEY,
        ClubId INT NOT NULL REFERENCES Clubs(ClubId) ON DELETE CASCADE,
        Title NVARCHAR(200) NOT NULL,
        VenueText NVARCHAR(200) NULL,
        EventDate DATETIME2 NOT NULL,
        RegistrationDeadline DATETIME2 NOT NULL,
        Capacity INT NOT NULL CONSTRAINT CK_Events_Capacity CHECK (Capacity > 0),
        Status NVARCHAR(20) NOT NULL DEFAULT 'draft'
            CONSTRAINT CK_Events_Status CHECK (Status IN ('draft', 'published', 'completed', 'cancelled')),
        CreatedByUserId INT NOT NULL REFERENCES Users(UserId),
        CONSTRAINT CK_Deadline_Before_Event CHECK (RegistrationDeadline <= EventDate)
    );
    CREATE INDEX IX_Events_ClubId_Date ON Events(ClubId, EventDate);
    CREATE INDEX IX_Events_Status ON Events(Status);
END;

-- 7. Event Registrations Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EventRegistrations')
BEGIN
    CREATE TABLE EventRegistrations (
        RegistrationId INT IDENTITY(1,1) PRIMARY KEY,
        EventId INT NOT NULL REFERENCES Events(EventId) ON DELETE CASCADE,
        UserId INT NOT NULL REFERENCES Users(UserId),
        Status NVARCHAR(20) NOT NULL DEFAULT 'confirmed'
            CONSTRAINT CK_EventRegistrations_Status CHECK (Status IN ('confirmed', 'waitlisted', 'cancelled')),
        RegisteredAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_Event_User_Reg UNIQUE (EventId, UserId)
    );
    CREATE INDEX IX_Reg_EventId_Status ON EventRegistrations(EventId, Status);
END;

-- 8. Attendance Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Attendance')
BEGIN
    CREATE TABLE Attendance (
        AttendanceId INT IDENTITY(1,1) PRIMARY KEY,
        EventId INT NOT NULL REFERENCES Events(EventId) ON DELETE CASCADE,
        UserId INT NOT NULL REFERENCES Users(UserId),
        CheckedInAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        RecordedByUserId INT NOT NULL REFERENCES Users(UserId),
        CONSTRAINT UQ_Event_User_Att UNIQUE (EventId, UserId)
    );
    CREATE INDEX IX_Attendance_EventId ON Attendance(EventId);
END;

-- 9. Club Proposals Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ClubProposals')
BEGIN
    CREATE TABLE ClubProposals (
        ProposalId INT IDENTITY(1,1) PRIMARY KEY,
        ApplicantUserId INT NOT NULL REFERENCES Users(UserId),
        ProposedName NVARCHAR(150) NOT NULL,
        DepartmentId INT NOT NULL REFERENCES Departments(DepartmentId),
        Description NVARCHAR(MAX) NOT NULL,
        Status NVARCHAR(20) NOT NULL DEFAULT 'submitted'
            CONSTRAINT CK_ClubProposals_Status CHECK (Status IN ('submitted', 'changes_requested', 'approved', 'rejected')),
        SubmittedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Proposals_Dept_Status ON ClubProposals(DepartmentId, Status);
END;

-- 10. Approvals Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Approvals')
BEGIN
    CREATE TABLE Approvals (
        ApprovalId INT IDENTITY(1,1) PRIMARY KEY,
        ProposalId INT NOT NULL REFERENCES ClubProposals(ProposalId) ON DELETE CASCADE,
        ReviewerUserId INT NOT NULL REFERENCES Users(UserId),
        Stage NVARCHAR(20) NOT NULL CONSTRAINT CK_Approvals_Stage CHECK (Stage IN ('faculty', 'hod')),
        Decision NVARCHAR(20) NOT NULL CONSTRAINT CK_Approvals_Decision CHECK (Decision IN ('approve', 'reject', 'changes_requested')),
        Comment NVARCHAR(MAX) NULL,
        DecidedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Approvals_ProposalId ON Approvals(ProposalId);
END;

-- 11. Event Outcomes Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EventOutcomes')
BEGIN
    CREATE TABLE EventOutcomes (
        OutcomeId INT IDENTITY(1,1) PRIMARY KEY,
        EventId INT NOT NULL UNIQUE REFERENCES Events(EventId) ON DELETE CASCADE,
        Summary NVARCHAR(MAX) NULL,
        AttendanceCountSnapshot INT NOT NULL DEFAULT 0,
        SubmittedByUserId INT NOT NULL REFERENCES Users(UserId),
        SubmittedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;

-- 12. Notifications Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Notifications')
BEGIN
    CREATE TABLE Notifications (
        NotificationId INT IDENTITY(1,1) PRIMARY KEY,
        UserId INT NOT NULL REFERENCES Users(UserId) ON DELETE CASCADE,
        Type NVARCHAR(50) NOT NULL,
        Message NVARCHAR(500) NOT NULL,
        IsRead BIT NOT NULL DEFAULT 0,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Notif_UserId_IsRead ON Notifications(UserId, IsRead);
END;

-- 13. Audit Logs Table (Synchronous Security Trail)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AuditLogs')
BEGIN
    CREATE TABLE AuditLogs (
        AuditLogId INT IDENTITY(1,1) PRIMARY KEY,
        ActorUserId INT NOT NULL REFERENCES Users(UserId),
        Action NVARCHAR(100) NOT NULL,
        EntityType NVARCHAR(50) NOT NULL,
        EntityId INT NOT NULL,
        Details NVARCHAR(MAX) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Audit_Entity ON AuditLogs(EntityType, EntityId);
    CREATE INDEX IX_Audit_Actor_Date ON AuditLogs(ActorUserId, CreatedAt);
END;

-- 14. Uploaded Files Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'UploadedFiles')
BEGIN
    CREATE TABLE UploadedFiles (
        FileId NVARCHAR(64) PRIMARY KEY,
        OwnerUserId INT NOT NULL REFERENCES Users(UserId),
        EntityType NVARCHAR(50) NOT NULL,
        EntityId INT NOT NULL,
        OriginalFilename NVARCHAR(255) NOT NULL,
        BlobPath NVARCHAR(500) NOT NULL,
        MimeType NVARCHAR(100) NOT NULL,
        FileSizeBytes INT NOT NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Uploads_Entity ON UploadedFiles(EntityType, EntityId);
END;
