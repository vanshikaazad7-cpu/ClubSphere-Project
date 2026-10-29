import json
from typing import Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog


def record_audit_log(
    db: Session,
    actor_user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    details: Optional[Union[str, Dict[str, Any]]] = None,
) -> AuditLog:
    """Record an immutable-style audit log entry synchronously within the active DB transaction.

    CRITICAL SECURITY REQUIREMENT:
    This operation adds the AuditLog record to the existing session.
    The caller must commit the transaction so both the state change and the audit log
    commit atomically, or roll back together if an error occurs.
    """
    serialized_details = None
    if details is not None:
        if isinstance(details, str):
            serialized_details = details
        else:
            serialized_details = json.dumps(details, default=str)

    log_entry = AuditLog(
        ActorUserId=actor_user_id,
        Action=action,
        EntityType=entity_type,
        EntityId=entity_id,
        Details=serialized_details,
    )
    db.add(log_entry)
    db.flush()  # Ensures foreign key / DB validation occurs immediately in this transaction
    return log_entry
