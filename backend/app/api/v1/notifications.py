from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rbac import get_current_active_user
from app.models.models import Notification, User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
def get_user_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve in-app notifications for the authenticated user."""
    notifications = (
        db.query(Notification)
        .filter(Notification.UserId == current_user.UserId)
        .order_by(Notification.CreatedAt.desc())
        .limit(100)
        .all()
    )

    unread_count = (
        db.query(Notification)
        .filter(
            Notification.UserId == current_user.UserId,
            Notification.IsRead == False,  # noqa: E712
        )
        .count()
    )

    items = [
        NotificationResponse(
            notification_id=n.NotificationId,
            user_id=n.UserId,
            type=n.Type,
            message=n.Message,
            is_read=n.IsRead,
            created_at=n.CreatedAt,
        )
        for n in notifications
    ]

    return NotificationListResponse(items=items, total=len(items), unread_count=unread_count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.NotificationId == notification_id,
            Notification.UserId == current_user.UserId,
        )
        .first()
    )

    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.IsRead = True
    db.commit()
    db.refresh(notif)

    return NotificationResponse(
        notification_id=notif.NotificationId,
        user_id=notif.UserId,
        type=notif.Type,
        message=notif.Message,
        is_read=notif.IsRead,
        created_at=notif.CreatedAt,
    )


@router.put("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark all unread notifications for the current user as read."""
    db.query(Notification).filter(
        Notification.UserId == current_user.UserId,
        Notification.IsRead == False,  # noqa: E712
    ).update({"IsRead": True})
    db.commit()
    return {"message": "All notifications marked as read"}
