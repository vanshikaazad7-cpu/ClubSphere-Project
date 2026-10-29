from app.models.models import Notification


def test_notifications_lifecycle(client, student_token, student_user, db_session):
    # Create test notification
    n = Notification(
        UserId=student_user.UserId,
        Type="SYSTEM_ALERT",
        Message="Welcome to ClubSphere system testing.",
        IsRead=False,
    )
    db_session.add(n)
    db_session.commit()
    db_session.refresh(n)

    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Get notifications
    get_res = client.get("/api/v1/notifications", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["unread_count"] >= 1
    assert any(item["notification_id"] == n.NotificationId for item in data["items"])

    # 2. Mark specific notification as read
    read_res = client.put(f"/api/v1/notifications/{n.NotificationId}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 3. Mark all read
    all_read = client.put("/api/v1/notifications/read-all", headers=headers)
    assert all_read.status_code == 200


def test_analytics_overview_calculation(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_clubs" in data
    assert "active_clubs" in data
    assert "total_events" in data
    assert "avg_attendance_rate" in data
    assert "branch_metrics" in data
    assert isinstance(data["branch_metrics"], list)
