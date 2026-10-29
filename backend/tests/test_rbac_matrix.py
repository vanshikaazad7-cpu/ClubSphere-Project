import pytest
from app.models.models import RoleNameEnum


@pytest.mark.parametrize(
    "role_token_fixture",
    ["student_token", "manager_token", "faculty_token", "hod_token"],
)
def test_admin_audit_logs_denied_for_non_admins(client, request, role_token_fixture):
    """Verify that non-Admin roles receive 403 Forbidden when accessing audit logs."""
    token = request.getfixturevalue(role_token_fixture)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]


@pytest.mark.parametrize(
    "role_token_fixture",
    ["student_token", "manager_token", "faculty_token", "hod_token"],
)
def test_admin_direct_club_create_denied_for_non_admins(client, request, role_token_fixture):
    """Verify that non-Admin roles cannot create clubs directly (must use proposal workflow)."""
    token = request.getfixturevalue(role_token_fixture)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Unauthorized Club",
        "program_id": 1,
        "manager_user_id": 1,
    }
    response = client.post("/api/v1/clubs", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize(
    "role_token_fixture",
    ["student_token", "manager_token"],
)
def test_proposal_review_denied_for_students_and_managers(client, request, role_token_fixture):
    """Verify that ordinary students and club managers cannot review club proposals."""
    token = request.getfixturevalue(role_token_fixture)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"decision": "approve"}
    response = client.post("/api/v1/proposals/1/review", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Only Faculty, HOD, or Administrator" in response.json()["detail"]


def test_admin_can_access_audit_logs(client, admin_token):
    """Verify that Administrator can successfully access audit logs."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()


def test_admin_can_access_analytics(client, admin_token):
    """Verify that Administrator can access institutional analytics."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert response.status_code == 200
    assert "active_clubs" in response.json()


def test_unauthenticated_protected_route_returns_401(client):
    """Verify that unauthenticated access returns 401 Unauthorized."""
    response = client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 401
