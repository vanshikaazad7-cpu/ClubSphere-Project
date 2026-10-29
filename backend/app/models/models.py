import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoleNameEnum(str, enum.Enum):
    STUDENT = "Student"
    CLUB_MANAGER = "Club Manager"
    FACULTY = "Faculty"
    HOD = "HOD"
    ADMINISTRATOR = "Administrator"


class Branch(Base):
    """A top-level academic track, e.g. 'B.Tech', 'M.Tech', 'MBA'.

    Parent of :class:`Program`. Seeded from ``app/data/branches.json``.
    """

    __tablename__ = "Branches"

    BranchId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Stable string id from the JSON source, e.g. 'btech'.
    BranchKey = Column(String(50), unique=True, nullable=False)
    Name = Column(String(150), unique=True, nullable=False)
    # 'undergraduate' | 'postgraduate' | 'doctoral'
    DegreeLevel = Column(String(50), nullable=False)
    # Controls presentation order in the UI dropdowns.
    SortOrder = Column(Integer, nullable=False, default=0)

    programs = relationship("Program", back_populates="branch")


class Program(Base):
    """A specialization within a branch, e.g. 'B.Tech - Artificial Intelligence & Machine Learning'.

    Seeded from ``app/data/programs.json``. Users, clubs, and proposals all point here.
    """

    __tablename__ = "Programs"

    ProgramId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Stable string id from the JSON source, e.g. 'btech_aiml'.
    ProgramKey = Column(String(100), unique=True, nullable=False)
    BranchId = Column(Integer, ForeignKey("Branches.BranchId"), nullable=False, index=True)
    Name = Column(String(150), nullable=False)
    # Human-readable label shown in the UI, e.g. 'B.Tech - AI/ML'.
    FullName = Column(String(255), nullable=False)
    # Optional industry partner, e.g. 'Microsoft', 'Google', 'IBM'.
    CollaborationPartner = Column(String(150), nullable=True)
    SortOrder = Column(Integer, nullable=False, default=0)

    branch = relationship("Branch", back_populates="programs", lazy="joined")
    users = relationship("User", back_populates="program")
    clubs = relationship("Club", back_populates="program")
    proposals = relationship("ClubProposal", back_populates="program")


class Role(Base):
    __tablename__ = "Roles"

    RoleId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    RoleName = Column(String(30), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "Users"

    UserId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Email = Column(String(256), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(256), nullable=False)
    FullName = Column(String(150), nullable=False)
    RoleId = Column(Integer, ForeignKey("Roles.RoleId"), nullable=False)
    ProgramId = Column(Integer, ForeignKey("Programs.ProgramId"), nullable=True)
    IsActive = Column(Boolean, nullable=False, default=True)
    TokenVersion = Column(Integer, nullable=False, default=1)
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)

    role = relationship("Role", back_populates="users", lazy="joined")
    program = relationship("Program", back_populates="users", lazy="joined")
    managed_clubs = relationship("Club", back_populates="manager")
    memberships = relationship("ClubMembership", back_populates="user")
    registrations = relationship("EventRegistration", back_populates="user")
    attendances = relationship("Attendance", foreign_keys="Attendance.UserId", back_populates="user")
    proposals = relationship("ClubProposal", back_populates="applicant")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Club(Base):
    __tablename__ = "Clubs"

    ClubId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Name = Column(String(150), unique=True, nullable=False, index=True)
    ProgramId = Column(Integer, ForeignKey("Programs.ProgramId"), nullable=False)
    ManagerUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Description = Column(Text, nullable=True)
    Status = Column(String(20), nullable=False, default="pending")
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("Status IN ('pending', 'active', 'suspended')", name="CK_Clubs_Status"),
    )

    program = relationship("Program", back_populates="clubs", lazy="joined")
    manager = relationship("User", back_populates="managed_clubs", lazy="joined")
    members = relationship("ClubMembership", back_populates="club", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="club", cascade="all, delete-orphan")


class ClubMembership(Base):
    __tablename__ = "ClubMemberships"

    MembershipId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ClubId = Column(Integer, ForeignKey("Clubs.ClubId", ondelete="CASCADE"), nullable=False)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Status = Column(String(20), nullable=False, default="requested")
    Role = Column(String(30), nullable=False, default="Member")  # 'Member' or 'Lead'
    JoinedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("ClubId", "UserId", name="UQ_Club_User"),
        CheckConstraint("Status IN ('requested', 'active', 'removed')", name="CK_ClubMemberships_Status"),
    )

    club = relationship("Club", back_populates="members")
    user = relationship("User", back_populates="memberships", lazy="joined")


class Event(Base):
    __tablename__ = "Events"

    EventId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ClubId = Column(Integer, ForeignKey("Clubs.ClubId", ondelete="CASCADE"), nullable=False)
    Title = Column(String(200), nullable=False)
    VenueText = Column(String(200), nullable=True)
    EventDate = Column(DateTime, nullable=False)
    RegistrationDeadline = Column(DateTime, nullable=False)
    Capacity = Column(Integer, nullable=False)
    Status = Column(String(20), nullable=False, default="draft")
    CreatedByUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)

    __table_args__ = (
        CheckConstraint("Capacity > 0", name="CK_Events_Capacity"),
        CheckConstraint("Status IN ('draft', 'published', 'completed', 'cancelled')", name="CK_Events_Status"),
        CheckConstraint("RegistrationDeadline <= EventDate", name="CK_Deadline_Before_Event"),
        Index("IX_Events_ClubId_Date", "ClubId", "EventDate"),
    )

    club = relationship("Club", back_populates="events", lazy="joined")
    creator = relationship("User", foreign_keys=[CreatedByUserId])
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="event", cascade="all, delete-orphan")
    outcome = relationship("EventOutcome", back_populates="event", uselist=False, cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "EventRegistrations"

    RegistrationId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    EventId = Column(Integer, ForeignKey("Events.EventId", ondelete="CASCADE"), nullable=False)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Status = Column(String(20), nullable=False, default="confirmed")
    RegisteredAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("EventId", "UserId", name="UQ_Event_User_Reg"),
        CheckConstraint("Status IN ('confirmed', 'waitlisted', 'cancelled')", name="CK_EventRegistrations_Status"),
        Index("IX_Reg_EventId_Status", "EventId", "Status"),
    )

    event = relationship("Event", back_populates="registrations")
    user = relationship("User", back_populates="registrations", lazy="joined")


class Attendance(Base):
    __tablename__ = "Attendance"

    AttendanceId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    EventId = Column(Integer, ForeignKey("Events.EventId", ondelete="CASCADE"), nullable=False)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    CheckedInAt = Column(DateTime, nullable=False, default=utc_now)
    RecordedByUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)

    __table_args__ = (
        UniqueConstraint("EventId", "UserId", name="UQ_Event_User_Att"),
    )

    event = relationship("Event", back_populates="attendances")
    user = relationship("User", foreign_keys=[UserId], back_populates="attendances", lazy="joined")
    recorded_by = relationship("User", foreign_keys=[RecordedByUserId])


class ClubProposal(Base):
    __tablename__ = "ClubProposals"

    ProposalId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ApplicantUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    ProposedName = Column(String(150), nullable=False)
    ProgramId = Column(Integer, ForeignKey("Programs.ProgramId"), nullable=False)
    Description = Column(Text, nullable=False)
    Status = Column(String(20), nullable=False, default="submitted")
    SubmittedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("Status IN ('submitted', 'changes_requested', 'approved', 'rejected')", name="CK_ClubProposals_Status"),
    )

    applicant = relationship("User", back_populates="proposals", lazy="joined")
    program = relationship("Program", back_populates="proposals", lazy="joined")
    approvals = relationship("Approval", back_populates="proposal", cascade="all, delete-orphan", order_by="Approval.DecidedAt")


class Approval(Base):
    __tablename__ = "Approvals"

    ApprovalId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ProposalId = Column(Integer, ForeignKey("ClubProposals.ProposalId", ondelete="CASCADE"), nullable=False)
    ReviewerUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Stage = Column(String(20), nullable=False)
    Decision = Column(String(20), nullable=False)
    Comment = Column(Text, nullable=True)
    DecidedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("Stage IN ('faculty', 'hod')", name="CK_Approvals_Stage"),
        CheckConstraint("Decision IN ('approve', 'reject', 'changes_requested')", name="CK_Approvals_Decision"),
    )

    proposal = relationship("ClubProposal", back_populates="approvals")
    reviewer = relationship("User", lazy="joined")


class EventOutcome(Base):
    __tablename__ = "EventOutcomes"

    OutcomeId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    EventId = Column(Integer, ForeignKey("Events.EventId", ondelete="CASCADE"), unique=True, nullable=False)
    Summary = Column(Text, nullable=True)
    AttendanceCountSnapshot = Column(Integer, nullable=False, default=0)
    SubmittedByUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    SubmittedAt = Column(DateTime, nullable=False, default=utc_now)

    event = relationship("Event", back_populates="outcome")
    submitted_by = relationship("User")


class Notification(Base):
    __tablename__ = "Notifications"

    NotificationId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Type = Column(String(50), nullable=False)
    Message = Column(String(500), nullable=False)
    IsRead = Column(Boolean, nullable=False, default=False)
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        Index("IX_Notif_UserId_IsRead", "UserId", "IsRead"),
    )

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "AuditLogs"

    AuditLogId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ActorUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Action = Column(String(100), nullable=False)
    EntityType = Column(String(50), nullable=False)
    EntityId = Column(Integer, nullable=False)
    Details = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        Index("IX_Audit_Entity", "EntityType", "EntityId"),
    )

    actor = relationship("User", lazy="joined")


class UploadedFile(Base):
    __tablename__ = "UploadedFiles"

    FileId = Column(String(64), primary_key=True, index=True)
    OwnerUserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    EntityType = Column(String(50), nullable=False)
    EntityId = Column(Integer, nullable=False)
    OriginalFilename = Column(String(255), nullable=False)
    BlobPath = Column(String(500), nullable=False)
    MimeType = Column(String(100), nullable=False)
    FileSizeBytes = Column(Integer, nullable=False)
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)

    owner = relationship("User")
