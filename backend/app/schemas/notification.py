from datetime import datetime
from typing import List
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    notification_id: int
    user_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
