from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlmodel import select

from backend.src.database import job_dir
from backend.src.models import Book
from backend.src.routers.books import process_job, run_vad
from backend.tests.conftest import VALID_SID

def test_run_vad_success(temp_data_dir):
    job_id = "test_run_vad"
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    input_file = d / "book.json"
    input_file.write_text('{"text": "hello"}')
    output_file = d / "vad.json"

    mock_resp = MagicMock()
    mock_resp.content = b'{"vad": {"1": [0.5, 0.5]}}'
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        run_vad(job_id, input_file, output_file)

        mock_post.assert_called_once()
        assert output_file.exists()
        assert output_file.read_bytes() == b'{"vad": {"1": [0.5, 0.5]}}'

def test_process_job_success(session, temp_data_dir):
    job_id = "process_success_job"
    book = Book(name="b.epub", job_id=job_id, browser_id=VALID_SID, status="queued")
    session.add(book)
    session.commit()

    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "book.epub").write_bytes(b"dummy epub")

    # Mock BookParser to write a dummy parsed file
    def fake_parse(epub_path, output_dir):
        (output_dir / "parsed_temp.json").write_text('{"chapter": "1"}')

    with patch("backend.src.routers.books.BookParser") as mock_parser_cls, \
         patch("backend.src.routers.books.run_vad") as mock_vad:
        mock_instance = MagicMock()
        mock_instance.parse.side_effect = fake_parse
        mock_parser_cls.return_value = mock_instance

        process_job(job_id)

        session.refresh(book)
        assert book.status == "done"
        assert (d / "book.json").exists()
        mock_vad.assert_called_once()

def test_process_job_failure(session, temp_data_dir):
    job_id = "process_failure_job"
    book = Book(name="b.epub", job_id=job_id, browser_id=VALID_SID, status="queued")
    session.add(book)
    session.commit()

    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)

    with patch("backend.src.routers.books.BookParser") as mock_parser_cls:
        mock_instance = MagicMock()
        mock_instance.parse.side_effect = RuntimeError("Parser crashed")
        mock_parser_cls.return_value = mock_instance

        process_job(job_id)

        session.refresh(book)
        assert book.status == "failed"
