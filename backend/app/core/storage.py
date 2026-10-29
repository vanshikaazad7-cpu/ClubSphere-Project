import os
import re
import uuid
from typing import Tuple
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import UploadedFile


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and injection attacks."""
    basename = os.path.basename(filename)
    # Remove any character that isn't alphanumeric, dot, underscore, or dash
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", basename)
    # Prevent hidden files or double dots
    cleaned = cleaned.lstrip(".")
    if not cleaned:
        cleaned = f"file_{uuid.uuid4().hex[:8]}"
    return cleaned


def validate_file(file: UploadFile) -> Tuple[str, int]:
    """Validate MIME type and content size against strict allowlist."""
    content_type = file.content_type or ""
    allowed_types = settings.ALLOWED_MIME_TYPES
    if isinstance(allowed_types, str):
        allowed_list = [t.strip() for t in allowed_types.split(",")]
    else:
        allowed_list = allowed_types

    if content_type.lower() not in [t.lower() for t in allowed_list]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Disallowed file type: {content_type}. Allowed types: {', '.join(allowed_list)}",
        )

    # Read bytes to check file size
    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)

    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
        )

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)",
        )

    return content_type, size_bytes


def store_blob_or_local(
    file_bytes: bytes,
    file_id: str,
    sanitized_name: str,
) -> str:
    """Save file to Azure Blob Storage if configured, or local upload dir for local dev."""
    blob_name = f"{file_id}_{sanitized_name}"

    if settings.AZURE_STORAGE_CONNECTION_STRING:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            container_client = blob_service_client.get_container_client(
                settings.AZURE_STORAGE_CONTAINER_NAME
            )
            if not container_client.exists():
                container_client.create_container()
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_bytes, overwrite=True)
            return blob_client.url
        except Exception:
            # Fall back to local storage if Azure SDK fails or connection is unreachable
            pass

    # Local fallback
    upload_dir = settings.LOCAL_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = os.path.join(upload_dir, blob_name)
    with open(destination_path, "wb") as f:
        f.write(file_bytes)
    return destination_path
