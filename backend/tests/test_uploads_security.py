import io
from app.core.config import settings


def test_upload_valid_file_success(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    file_content = b"%PDF-1.4 sample pdf content for club proposal"
    files = {"file": ("proposal_doc.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"entity_type": "ClubProposals", "entity_id": 1}

    response = client.post("/api/v1/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["original_filename"] == "proposal_doc.pdf"
    assert res_data["content_type"] == "application/pdf"
    assert res_data["size_bytes"] == len(file_content)
    assert "upload_id" in res_data


def test_upload_disallowed_mime_type_fails(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    file_content = b"MZ executable binary payload"
    files = {"file": ("malware.exe", io.BytesIO(file_content), "application/x-msdownload")}
    data = {"entity_type": "Clubs", "entity_id": 1}

    response = client.post("/api/v1/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 400
    assert "Disallowed file type" in response.json()["detail"]


def test_upload_empty_file_fails(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
    data = {"entity_type": "Clubs", "entity_id": 1}

    response = client.post("/api/v1/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_filename_sanitization_prevents_path_traversal(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    file_content = b"\x89PNG\r\n\x1a\n fake png data"
    # Attempt directory traversal attack in filename
    files = {"file": ("../../etc/passwd.png", io.BytesIO(file_content), "image/png")}
    data = {"entity_type": "Clubs", "entity_id": 1}

    response = client.post("/api/v1/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 201
    sanitized_name = response.json()["original_filename"]
    assert ".." not in sanitized_name
    assert "/" not in sanitized_name
    assert "\\" not in sanitized_name


def test_upload_oversized_file_fails(client, student_token, monkeypatch):
    headers = {"Authorization": f"Bearer {student_token}"}
    # Temporarily set max size to 50 bytes to test 413 without generating 10MB in test memory
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 50)

    file_content = b"A" * 100  # 100 bytes > 50 bytes limit
    files = {"file": ("large_image.png", io.BytesIO(file_content), "image/png")}
    data = {"entity_type": "Clubs", "entity_id": 1}

    response = client.post("/api/v1/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"].lower()
