from datetime import datetime, timedelta, timezone
from app.models.models import Event, EventRegistration


def test_attendance_and_outcomes_lifecycle(client, sample_club, manager_token, student_user, student_token, db_session):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # 1. Create a published event
    event = Event(
        ClubId=sample_club.ClubId,
        Title="Robotics Bootcamp",
        VenueText="Lab 2",
        EventDate=now + timedelta(days=2),
        RegistrationDeadline=now + timedelta(days=1),
        Capacity=30,
        Status="published",
        CreatedByUserId=sample_club.ManagerUserId,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    # 2. Student registers
    client.post(
        f"/api/v1/events/{event.EventId}/register",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # 3. Manager marks attendance for confirmed student
    att_res = client.post(
        f"/api/v1/events/{event.EventId}/attendance",
        json={"user_ids": [student_user.UserId]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert att_res.status_code == 200
    assert att_res.json()["marked_present"] == 1

    # 4. Attempt to mark attendance for unregistered user fails with 400
    att_fail = client.post(
        f"/api/v1/events/{event.EventId}/attendance",
        json={"user_ids": [9999]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert att_fail.status_code == 400
    assert "not confirmed registered" in att_fail.json()["detail"].lower()

    # 5. Manager submits event outcome report
    out_res = client.post(
        f"/api/v1/events/{event.EventId}/outcomes",
        json={"summary": "Bootcamp was successful with high hands-on engagement."},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert out_res.status_code == 201
    assert out_res.json()["attendance_count_snapshot"] == 1

    # 6. Verify event outcome query
    get_out = client.get(f"/api/v1/events/{event.EventId}/outcomes")
    assert get_out.status_code == 200
    assert "hands-on engagement" in get_out.json()["summary"]
