import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rbac import get_current_active_user
from app.core.storage import validate_file, sanitize_filename, store_blob_or_local
from app.models.models import UploadedFile, User
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/uploads", tags=["File Storage & Uploads"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_or_media(
    file: UploadFile = File(...),
    entity_type: str = Form(..., description="Target entity type, e.g. ClubProposals, Clubs, Events"),
    entity_id: int = Form(..., description="Target entity ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload proposal document, club logo, or event poster to Blob Storage with MIME/size security validation."""
    content_type, size_bytes = validate_file(file)

    # Read binary content
    file_bytes = await file.read()
    sanitized_name = sanitize_filename(file.filename or "upload.bin")
    file_id = uuid.uuid4().hex

    storage_url = store_blob_or_local(
        file_bytes=file_bytes,
        file_id=file_id,
        sanitized_name=sanitized_name,
    )

    db_file = UploadedFile(
        FileId=file_id,
        OwnerUserId=current_user.UserId,
        EntityType=entity_type,
        EntityId=entity_id,
        OriginalFilename=sanitized_name,
        BlobPath=storage_url,
        MimeType=content_type,
        FileSizeBytes=size_bytes,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return UploadResponse(
        upload_id=db_file.FileId,
        original_filename=db_file.OriginalFilename,
        entity_type=db_file.EntityType,
        entity_id=db_file.EntityId,
        content_type=db_file.MimeType,
        size_bytes=db_file.FileSizeBytes,
        url=storage_url,
        created_at=db_file.CreatedAt,
    )
