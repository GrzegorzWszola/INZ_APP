from datetime import timedelta
from sqlmodel import select

from backend.src.database import cleanup, job_dir, set_status
from backend.src.models import Book
from backend.src.models.books_models import utcnow

def test_set_status(session):
    book = Book(
        name="test.epub",
        job_id="job_status_test",
        browser_id="test_browser",
        status="queued"
    )
    session.add(book)
    session.commit()

    set_status("job_status_test", "predicting")

    session.refresh(book)
    assert book.status == "predicting"

def test_cleanup_deletes_stale_and_preserves_active(session, temp_data_dir):
    old_job_id = "old_job_123"
    fresh_job_id = "fresh_job_456"

    # Create directories
    old_dir = job_dir(old_job_id)
    old_dir.mkdir(parents=True, exist_ok=True)
    (old_dir / "test.txt").write_text("old data")

    fresh_dir = job_dir(fresh_job_id)
    fresh_dir.mkdir(parents=True, exist_ok=True)
    (fresh_dir / "test.txt").write_text("fresh data")

    # Insert books into db
    old_time = utcnow() - timedelta(days=5)
    fresh_time = utcnow() - timedelta(days=1)

    old_book = Book(
        name="old.epub",
        job_id=old_job_id,
        browser_id="browser1",
        status="done",
        last_seen=old_time,
    )
    fresh_book = Book(
        name="fresh.epub",
        job_id=fresh_job_id,
        browser_id="browser1",
        status="done",
        last_seen=fresh_time,
    )
    session.add(old_book)
    session.add(fresh_book)
    session.commit()

    # Run cleanup for books older than 3 days
    cleanup(day_number=3)

    remaining_books = session.exec(select(Book)).all()
    remaining_job_ids = [b.job_id for b in remaining_books]

    assert old_job_id not in remaining_job_ids
    assert fresh_job_id in remaining_job_ids

    # Check directory removal
    assert not old_dir.exists()
    assert fresh_dir.exists()

def test_cleanup_handles_missing_directory_gracefully(session, temp_data_dir):
    job_id = "missing_dir_job"
    old_time = utcnow() - timedelta(days=10)

    book = Book(
        name="ghost.epub",
        job_id=job_id,
        browser_id="browser1",
        status="done",
        last_seen=old_time,
    )
    session.add(book)
    session.commit()

    # Ensure dir doesn't exist
    assert not job_dir(job_id).exists()

    # Cleanup should not crash
    cleanup(day_number=3)

    remaining = session.exec(select(Book).where(Book.job_id == job_id)).first()
    assert remaining is None
