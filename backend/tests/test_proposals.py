from app.models.models import Club


def test_submit_club_proposal_success(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    payload = {
        "proposed_name": "Artificial Intelligence Club",
        "program_id": 1,
        "description": "A student club devoted to machine learning and AI research.",
    }
    response = client.post("/api/v1/proposals", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["proposed_name"] == "Artificial Intelligence Club"
    assert data["status"] == "submitted"
    assert "proposal_id" in data


def test_submit_duplicate_proposal_name_fails(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    payload = {
        "proposed_name": "Artificial Intelligence Club",
        "program_id": 1,
        "description": "Duplicate description.",
    }
    response = client.post("/api/v1/proposals", json=payload, headers=headers)
    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_faculty_recommendation_and_hod_approval_workflow(client, student_token, faculty_token, hod_token, db_session):
    # 1. Student submits proposal
    sub_res = client.post(
        "/api/v1/proposals",
        json={
            "proposed_name": "Cyber Security Club",
            "program_id": 1,
            "description": "Ethical hacking and defense club.",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert sub_res.status_code == 201
    prop_id = sub_res.json()["proposal_id"]

    # 2. Faculty review without comment on reject fails
    rej_fail = client.post(
        f"/api/v1/proposals/{prop_id}/review",
        json={"decision": "reject"},  # Missing comment
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert rej_fail.status_code == 422

    # 3. Faculty recommends (approves)
    fac_res = client.post(
        f"/api/v1/proposals/{prop_id}/review",
        json={"decision": "approve", "comment": "Excellent proposal. Recommended to HOD."},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert fac_res.status_code == 200

    # 4. HOD gives final approval -> Automatically activates Club!
    hod_res = client.post(
        f"/api/v1/proposals/{prop_id}/review",
        json={"decision": "approve", "comment": "Approved by HOD. Club is activated."},
        headers={"Authorization": f"Bearer {hod_token}"},
    )
    assert hod_res.status_code == 200
    data = hod_res.json()
    assert data["status"] == "approved"
    assert data["created_club_id"] is not None

    # Verify club actually exists in database
    club = db_session.query(Club).filter(Club.ClubId == data["created_club_id"]).first()
    assert club is not None
    assert club.Name == "Cyber Security Club"
    assert club.Status == "active"
