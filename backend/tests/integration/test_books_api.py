import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.src.database import job_dir
from backend.src.models import Book
from backend.tests.conftest import VALID_SID

def test_upload_epub_unauthenticated(unauth_client):
    response = unauth_client.post(
        "/books/upload_epub",
        files={"file": ("book.epub", b"dummy content", "application/epub+zip")}
    )
    assert response.status_code == 401

def test_upload_epub_invalid_extension(client):
    response = client.post(
        "/books/upload_epub",
        files={"file": ("notes.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == ".epub file required"

def test_upload_epub_success(client, session, monkeypatch):
    # Mock process_job background task to avoid executing external tools
    mock_called = []
    monkeypatch.setattr(
        "backend.src.routers.books.process_job",
        lambda job_id: mock_called.append(job_id)
    )

    dummy_epub = b"PK\x03\x04fake epub content"
    response = client.post(
        "/books/upload_epub",
        files={"file": ("my_novel.epub", io.BytesIO(dummy_epub), "application/epub+zip")}
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Verify database entry
    book = session.exec(select(Book).where(Book.job_id == job_id)).first()
    assert book is not None
    assert book.name == "my_novel.epub"
    assert book.status == "queued"
    assert book.browser_id == VALID_SID

    # Verify file saved on disk
    saved_file = job_dir(job_id) / "book.epub"
    assert saved_file.exists()
    assert saved_file.read_bytes() == dummy_epub

def test_upload_epub_file_too_large(client, monkeypatch):
    # Temporarily set MAX_BYTES to a tiny value to test 413
    monkeypatch.setattr("backend.src.routers.books.MAX_BYTES", 100)

    large_content = b"x" * 200
    response = client.post(
        "/books/upload_epub",
        files={"file": ("large.epub", io.BytesIO(large_content), "application/epub+zip")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File size too big"

def test_job_status(client, session):
    book = Book(
        name="test.epub",
        job_id="status_job_1",
        browser_id=VALID_SID,
        status="parsing"
    )
    session.add(book)
    session.commit()

    response = client.get("/books/status_job_1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "parsing"}

def test_job_status_session_isolation(client, session):
    # Book belonging to another session
    book = Book(
        name="other.epub",
        job_id="other_job_1",
        browser_id="other_user_session_token_1234567890",
        status="queued"
    )
    session.add(book)
    session.commit()

    # Current client has VALID_SID, so other's job should 404
    response = client.get("/books/other_job_1/status")
    assert response.status_code == 404

def test_get_content_still_processing(client, session):
    book = Book(
        name="test.epub",
        job_id="processing_job",
        browser_id=VALID_SID,
        status="predicting"
    )
    session.add(book)
    session.commit()

    response = client.get("/books/processing_job/content")
    assert response.status_code == 400
    assert response.json()["detail"] == "Book is still processing"

def test_get_content_done_success(client, session, temp_data_dir):
    job_id = "done_job_1"
    book = Book(
        name="test.epub",
        job_id=job_id,
        browser_id=VALID_SID,
        status="done"
    )
    session.add(book)
    session.commit()

    # Create book.json
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "book.json").write_text('{"title": "Sample Book"}')

    response = client.get(f"/books/{job_id}/content")
    assert response.status_code == 200
    assert response.json() == {"title": "Sample Book"}

def test_get_content_done_missing_file(client, session, temp_data_dir):
    job_id = "missing_file_job"
    book = Book(
        name="test.epub",
        job_id=job_id,
        browser_id=VALID_SID,
        status="done"
    )
    session.add(book)
    session.commit()

    # Ensure no book.json exists
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)

    response = client.get(f"/books/{job_id}/content")
    assert response.status_code == 404
    assert response.json()["detail"] == "Result not found"

def test_my_books(client, session):
    b1 = Book(name="b1.epub", job_id="j1", browser_id=VALID_SID, status="done")
    b2 = Book(name="b2.epub", job_id="j2", browser_id=VALID_SID, status="queued")
    b_other = Book(name="b3.epub", job_id="j3", browser_id="someone_else_1234567890123456", status="done")

    session.add_all([b1, b2, b_other])
    session.commit()

    response = client.get("/books/mine")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    job_ids = [b["job_id"] for b in items]
    assert "j1" in job_ids and "j2" in job_ids
    assert "j3" not in job_ids

def test_delete_book(client, session, temp_data_dir):
    job_id = "delete_me_job"
    book = Book(
        name="del.epub",
        job_id=job_id,
        browser_id=VALID_SID,
        status="done"
    )
    session.add(book)
    session.commit()

    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "book.json").write_text("{}")

    response = client.delete(f"/books/{job_id}")
    assert response.status_code == 204

    # DB record gone
    assert session.exec(select(Book).where(Book.job_id == job_id)).first() is None
    # Folder gone
    assert not d.exists()
