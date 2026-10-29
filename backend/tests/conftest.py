import os
import sys
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.models import (
    Role,
    RoleNameEnum,
    Branch,
    Program,
    User,
    Club,
    ClubMembership,
    Event,
    EventRegistration,
)

from sqlalchemy import event

# Use in-memory SQLite with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed Baseline Roles
        roles = {}
        for role_name in [
            RoleNameEnum.STUDENT.value,
            RoleNameEnum.CLUB_MANAGER.value,
            RoleNameEnum.FACULTY.value,
            RoleNameEnum.HOD.value,
            RoleNameEnum.ADMINISTRATOR.value,
        ]:
            r = Role(RoleName=role_name)
            db.add(r)
            roles[role_name] = r
        db.flush()

        # Seed Baseline Academic Data
        branch_btech = Branch(BranchKey="btech", Name="B.Tech", DegreeLevel="undergraduate", SortOrder=0)
        branch_mtech = Branch(BranchKey="mtech", Name="M.Tech", DegreeLevel="postgraduate", SortOrder=1)
        db.add_all([branch_btech, branch_mtech])
        db.flush()

        prog_cse = Program(
            ProgramKey="btech_cse", BranchId=branch_btech.BranchId,
            Name="Computer Science & Engineering",
            FullName="B.Tech - Computer Science & Engineering",
            CollaborationPartner=None, SortOrder=0,
        )
        prog_aiml = Program(
            ProgramKey="btech_aiml", BranchId=branch_btech.BranchId,
            Name="Artificial Intelligence & Machine Learning",
            FullName="B.Tech - AI/ML",
            CollaborationPartner=None, SortOrder=1,
        )
        prog_gen = Program(
            ProgramKey="gen", BranchId=branch_btech.BranchId,
            Name="General University Activities",
            FullName="General",
            CollaborationPartner=None, SortOrder=2,
        )
        db.add_all([prog_cse, prog_aiml, prog_gen])
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a fresh transactional database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provides a FastAPI test client with database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_test_user(db, email, full_name, role_name, program_key="btech_cse"):
    existing = db.query(User).filter(User.Email == email).first()
    if existing:
        return existing
    role = db.query(Role).filter(Role.RoleName == role_name).first()
    prog = db.query(Program).filter(Program.ProgramKey == program_key).first()
    user = User(
        Email=email,
        PasswordHash=get_password_hash("Password@123"),
        FullName=full_name,
        RoleId=role.RoleId,
        ProgramId=prog.ProgramId if prog else None,
        IsActive=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_user(db_session):
    return make_test_user(db_session, "student1@univ.edu", "Alice Student", RoleNameEnum.STUDENT.value)


@pytest.fixture
def student_token(student_user):
    return create_access_token(subject=student_user.UserId, role=RoleNameEnum.STUDENT.value)


@pytest.fixture
def student2_user(db_session):
    return make_test_user(db_session, "student2@univ.edu", "Bob Student", RoleNameEnum.STUDENT.value)


@pytest.fixture
def student2_token(student2_user):
    return create_access_token(subject=student2_user.UserId, role=RoleNameEnum.STUDENT.value)


@pytest.fixture
def manager_user(db_session):
    return make_test_user(db_session, "manager1@univ.edu", "Charlie Manager", RoleNameEnum.CLUB_MANAGER.value)


@pytest.fixture
def manager_token(manager_user):
    return create_access_token(subject=manager_user.UserId, role=RoleNameEnum.CLUB_MANAGER.value)


@pytest.fixture
def faculty_user(db_session):
    return make_test_user(db_session, "faculty1@univ.edu", "Dr. David Faculty", RoleNameEnum.FACULTY.value)


@pytest.fixture
def faculty_token(faculty_user):
    return create_access_token(subject=faculty_user.UserId, role=RoleNameEnum.FACULTY.value)


@pytest.fixture
def hod_user(db_session):
    return make_test_user(db_session, "hod1@univ.edu", "Dr. Eleanor HOD", RoleNameEnum.HOD.value)


@pytest.fixture
def hod_token(hod_user):
    return create_access_token(subject=hod_user.UserId, role=RoleNameEnum.HOD.value)


@pytest.fixture
def admin_user(db_session):
    return make_test_user(db_session, "admin1@univ.edu", "Frank Admin", RoleNameEnum.ADMINISTRATOR.value)


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(subject=admin_user.UserId, role=RoleNameEnum.ADMINISTRATOR.value)


@pytest.fixture
def sample_club(db_session, manager_user):
    existing = db_session.query(Club).filter(Club.Name == "Robotics Club").first()
    if existing:
        return existing
    dept = db_session.query(Program).filter(Program.ProgramKey == "btech_cse").first()
    club = Club(
        Name="Robotics Club",
        ProgramId=dept.ProgramId,
        ManagerUserId=manager_user.UserId,
        Description="Robotics innovation",
        Status="active",
    )
    db_session.add(club)
    db_session.commit()
    db_session.refresh(club)

    # Lead membership
    mem = ClubMembership(ClubId=club.ClubId, UserId=manager_user.UserId, Status="active", Role="Lead")
    db_session.add(mem)
    db_session.commit()
    return club


@pytest.fixture
def sample_event(db_session, sample_club, manager_user):
    existing = db_session.query(Event).filter(Event.Title == "AI Workshop").first()
    if existing:
        return existing
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ev = Event(
        ClubId=sample_club.ClubId,
        Title="AI Workshop",
        VenueText="Lab 101",
        EventDate=now + timedelta(days=7),
        RegistrationDeadline=now + timedelta(days=5),
        Capacity=2,  # Small capacity to test capacity limits
        Status="published",
        CreatedByUserId=manager_user.UserId,
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)
    return ev
