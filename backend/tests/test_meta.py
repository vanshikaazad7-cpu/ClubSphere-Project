def test_last_updated_is_public(client):
    """The landing page reads this without signing in."""
    response = client.get("/api/v1/meta/last-updated")
    assert response.status_code == 200


def test_last_updated_shape(client):
    response = client.get("/api/v1/meta/last-updated")
    data = response.json()
    assert "last_updated" in data
    assert "generated_at" in data
    assert set(data["counts"]) == {"clubs", "events", "registrations", "students"}
    for key in ("clubs", "events", "registrations", "students"):
        assert isinstance(data["counts"][key], int)


def test_last_updated_counts_track_the_database(client, db_session, sample_club, sample_event):
    """Counts come from the live tables, not a hard-coded summary."""
    response = client.get("/api/v1/meta/last-updated")
    counts = response.json()["counts"]
    assert counts["clubs"] >= 1
    assert counts["events"] >= 1
    assert counts["students"] >= 1


def test_last_updated_reflects_a_new_club(client, db_session, sample_club, manager_user):
    """A club created after the seed bumps the stamp and the club count."""
    before = client.get("/api/v1/meta/last-updated").json()
    before_clubs = before["counts"]["clubs"]

    from app.models.models import Club, Program
    dept = db_session.query(Program).filter(Program.ProgramKey == "btech_cse").first()
    club = Club(
        Name="Meta Test Club",
        ProgramId=dept.ProgramId,
        Description="Created to prove the last-updated stamp moves.",
        Status="active",
        ManagerUserId=manager_user.UserId,
    )
    db_session.add(club)
    db_session.commit()

    after = client.get("/api/v1/meta/last-updated").json()
    assert after["counts"]["clubs"] == before_clubs + 1
    assert after["last_updated"] is not None
    assert after["last_updated"] >= before["last_updated"]


def test_last_updated_exposes_no_record_content(client):
    """Public endpoint must not leak rows, only aggregate counts."""
    response = client.get("/api/v1/meta/last-updated")
    body = response.text.lower()
    for leak in ("password", "email", "description", "fullname", "full_name"):
        assert leak not in body
