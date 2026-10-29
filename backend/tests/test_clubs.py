def test_list_clubs_public(client, sample_club):
    response = client.get("/api/v1/clubs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any(c["club_id"] == sample_club.ClubId for c in data["items"])


def test_get_club_details(client, sample_club):
    response = client.get(f"/api/v1/clubs/{sample_club.ClubId}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_club.Name
    assert data["club_id"] == sample_club.ClubId


def test_join_club_success(client, sample_club, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.post(f"/api/v1/clubs/{sample_club.ClubId}/join", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "requested"
    assert data["club_id"] == sample_club.ClubId


def test_join_club_duplicate_fails(client, sample_club, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    # Second join attempt
    response = client.post(f"/api/v1/clubs/{sample_club.ClubId}/join", headers=headers)
    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_list_club_members_by_manager(client, sample_club, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = client.get(f"/api/v1/clubs/{sample_club.ClubId}/members", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


def test_list_club_members_denied_for_unauthorized_student(client, sample_club, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.get(f"/api/v1/clubs/{sample_club.ClubId}/members", headers=headers)
    assert response.status_code == 403


def test_update_membership_status(client, sample_club, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    # First get members
    members_res = client.get(f"/api/v1/clubs/{sample_club.ClubId}/members", headers=headers)
    items = members_res.json()["items"]
    requested_mem = next((m for m in items if m["status"] == "requested"), items[0])

    update_res = client.put(
        f"/api/v1/clubs/{sample_club.ClubId}/members/{requested_mem['membership_id']}",
        json={"status": "active", "role": "Member"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "active"


def test_update_club_profile_by_manager(client, sample_club, manager_token):
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = client.put(
        f"/api/v1/clubs/{sample_club.ClubId}",
        json={"description": "Updated Robotics description"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated Robotics description"


def test_update_club_profile_denied_for_other_user(client, sample_club, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.put(
        f"/api/v1/clubs/{sample_club.ClubId}",
        json={"description": "Hacked description"},
        headers=headers,
    )
    assert response.status_code == 403
