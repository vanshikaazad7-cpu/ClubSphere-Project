from datetime import datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: str
    original_filename: str
    entity_type: str
    entity_id: int
    content_type: str
    size_bytes: int
    url: str
    created_at: datetime
