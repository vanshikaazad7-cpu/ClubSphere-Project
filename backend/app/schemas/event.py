from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class EventCreateRequest(BaseModel):
    club_id: int
    title: str = Field(..., min_length=2, max_length=200)
    venue_text: Optional[str] = Field(None, max_length=200)
    event_date: datetime
    registration_deadline: datetime
    capacity: int = Field(..., gt=0, description="Capacity must be greater than zero")
    status: Optional[str] = Field("draft", pattern="^(draft|published|completed|cancelled)$")

    @model_validator(mode="after")
    def validate_deadline_before_event(self) -> "EventCreateRequest":
        if self.registration_deadline > self.event_date:
            raise ValueError("Registration deadline must be earlier than or equal to the event date")
        return self


class EventUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    venue_text: Optional[str] = None
    event_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    capacity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(draft|published|completed|cancelled)$")

    @model_validator(mode="after")
    def validate_dates(self) -> "EventUpdateRequest":
        if self.event_date and self.registration_deadline:
            if self.registration_deadline > self.event_date:
                raise ValueError("Registration deadline must be earlier than or equal to the event date")
        return self


class EventResponse(BaseModel):
    event_id: int
    club_id: int
    club_name: Optional[str] = None
    title: str
    venue_text: Optional[str] = None
    event_date: datetime
    registration_deadline: datetime
    capacity: int
    status: str
    created_by_user_id: int
    confirmed_registrations: int = 0
    seats_left: int = 0

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    page: int
    page_size: int


class RegistrationResponse(BaseModel):
    registration_id: int
    event_id: int
    user_id: int
    status: str
    registered_at: datetime


class RegistrationRosterItem(BaseModel):
    registration_id: int
    event_id: int
    user_id: int
    full_name: str
    email: str
    status: str
    registered_at: datetime
    attended: bool = False


class RegistrationListResponse(BaseModel):
    items: List[RegistrationRosterItem]
    total: int
    page: int
    page_size: int


class AttendanceRecordRequest(BaseModel):
    user_ids: List[int] = Field(..., min_length=1, description="List of user IDs to mark present")


class AttendanceResponse(BaseModel):
    event_id: int
    marked_present: int
    total_confirmed: int


class EventOutcomeCreateRequest(BaseModel):
    summary: str = Field(..., min_length=5)
    attendance_count_snapshot: Optional[int] = None


class EventOutcomeResponse(BaseModel):
    outcome_id: int
    event_id: int
    summary: Optional[str] = None
    attendance_count_snapshot: int
    submitted_by_user_id: int
    submitted_at: datetime

    class Config:
        from_attributes = True
