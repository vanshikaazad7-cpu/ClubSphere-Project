import pytest
from app.models.models import AuditLog, ClubProposal, Club
from app.core.audit import record_audit_log


def test_audit_log_written_synchronously_on_approval(client, student_token, hod_token, db_session):
    """Verify that an AuditLog entry is written synchronously when a proposal is approved."""
    # Submit proposal
    res1 = client.post(
        "/api/v1/proposals",
        json={
            "proposed_name": "Web Dev Society",
            "program_id": 1,
            "description": "Full-stack development club.",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    prop_id = res1.json()["proposal_id"]

    # Count audit logs before
    initial_audit_count = db_session.query(AuditLog).filter(
        AuditLog.EntityType == "ClubProposals",
        AuditLog.EntityId == prop_id,
    ).count()

    # HOD reviews and approves
    client.post(
        f"/api/v1/proposals/{prop_id}/review",
        json={"decision": "approve", "comment": "Approved."},
        headers={"Authorization": f"Bearer {hod_token}"},
    )

    # Count audit logs after
    after_audit_count = db_session.query(AuditLog).filter(
        AuditLog.EntityType == "ClubProposals",
        AuditLog.EntityId == prop_id,
    ).count()

    assert after_audit_count > initial_audit_count
    latest_log = db_session.query(AuditLog).filter(
        AuditLog.EntityType == "ClubProposals",
        AuditLog.EntityId == prop_id,
    ).order_by(AuditLog.CreatedAt.desc()).first()

    assert latest_log is not None
    assert "APPROVED" in latest_log.Action


def test_transactional_rollback_if_audit_fails(db_session, student_user):
    """Verify that if audit log write fails, the entire transaction rolls back atomically."""
    # Start a transaction: attempt to create a proposal, then force an audit failure
    proposal = ClubProposal(
        ApplicantUserId=student_user.UserId,
        ProposedName="Uncommitted Rollback Club",
        ProgramId=1,
        Description="This should never commit if audit fails.",
        Status="submitted",
    )
    db_session.add(proposal)
    db_session.flush()

    # Simulate audit write failure by passing invalid foreign key or forced error
    try:
        # Invalid ActorUserId will violate foreign key constraint or trigger exception
        record_audit_log(
            db=db_session,
            actor_user_id=9999999,  # Non-existent user
            action="TEST_FAILURE",
            entity_type="ClubProposals",
            entity_id=proposal.ProposalId,
        )
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Verify that proposal was NOT committed
    retrieved = db_session.query(ClubProposal).filter(
        ClubProposal.ProposedName == "Uncommitted Rollback Club"
    ).first()
    assert retrieved is None, "Proposal should have rolled back when audit log failed"
