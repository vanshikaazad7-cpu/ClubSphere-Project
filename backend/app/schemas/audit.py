from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    audit_log_id: int
    actor_user_id: int
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: int
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
