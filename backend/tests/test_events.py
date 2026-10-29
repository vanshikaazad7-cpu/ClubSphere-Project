from datetime import datetime, timedelta, timezone
from app.models.models import Event


def test_create_event_success(client, sample_club, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    now = datetime.now(timezone.utc)
    payload = {
        "club_id": sample_club.ClubId,
        "title": "Hackathon 2026",
        "venue_text": "Main Auditorium",
        "event_date": (now + timedelta(days=10)).isoformat(),
        "registration_deadline": (now + timedelta(days=8)).isoformat(),
        "capacity": 50,
        "status": "published",
    }
    response = client.post("/api/v1/events", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Hackathon 2026"
    assert data["capacity"] == 50
    assert data["seats_left"] == 50


def test_create_event_deadline_after_event_fails(client, sample_club, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    now = datetime.now(timezone.utc)
    payload = {
        "club_id": sample_club.ClubId,
        "title": "Invalid Date Event",
        "event_date": (now + timedelta(days=5)).isoformat(),
        "registration_deadline": (now + timedelta(days=8)).isoformat(),  # After event!
        "capacity": 20,
    }
    response = client.post("/api/v1/events", json=payload, headers=headers)
    assert response.status_code == 422


def test_event_registration_success(client, sample_event, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.post(f"/api/v1/events/{sample_event.EventId}/register", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["event_id"] == sample_event.EventId


def test_event_registration_duplicate_fails(client, sample_event, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    # Duplicate attempt
    response = client.post(f"/api/v1/events/{sample_event.EventId}/register", headers=headers)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_event_capacity_exhaustion_fails(client, sample_event, student2_token, admin_token):
    # sample_event has Capacity = 2. student1 already registered.
    # Now student2 registers (reaching 2/2)
    headers2 = {"Authorization": f"Bearer {student2_token}"}
    res2 = client.post(f"/api/v1/events/{sample_event.EventId}/register", headers=headers2)
    assert res2.status_code == 201

    # Now a 3rd user (admin acting as student) attempts to register when capacity is full
    headers3 = {"Authorization": f"Bearer {admin_token}"}
    res3 = client.post(f"/api/v1/events/{sample_event.EventId}/register", headers=headers3)
    assert res3.status_code == 409
    assert "capacity" in res3.json()["detail"].lower()


def test_event_past_deadline_rejected(client, db_session, sample_club, student_token):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    past_event = Event(
        ClubId=sample_club.ClubId,
        Title="Expired Event",
        EventDate=now + timedelta(days=1),
        RegistrationDeadline=now - timedelta(hours=2),  # In the past!
        Capacity=50,
        Status="published",
        CreatedByUserId=sample_club.ManagerUserId,
    )
    db_session.add(past_event)
    db_session.commit()
    db_session.refresh(past_event)

    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.post(f"/api/v1/events/{past_event.EventId}/register", headers=headers)
    assert response.status_code == 400
    assert "deadline" in response.json()["detail"].lower()


def test_cancel_registration(client, sample_event, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.delete(f"/api/v1/events/{sample_event.EventId}/register", headers=headers)
    assert response.status_code == 200
    assert "cancelled" in response.json()["message"]


def test_get_my_registrations(client, sample_event, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    # Register for sample_event
    client.post(f"/api/v1/events/{sample_event.EventId}/register", headers=headers)
    response = client.get("/api/v1/events/my-registrations", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert any(r["event_id"] == sample_event.EventId and r["status"] == "confirmed" for r in items)
