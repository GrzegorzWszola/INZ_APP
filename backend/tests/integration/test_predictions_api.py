import json
from backend.src.database import job_dir
from backend.src.models import Book
from backend.tests.conftest import VALID_SID

def test_predictions_unauthenticated(unauth_client):
    response = unauth_client.post("/predictions/job123", json={"sentence_ids": [1, 2]})
    assert response.status_code == 401

def test_predictions_unknown_book(client):
    response = client.post("/predictions/nonexistent_job", json={"sentence_ids": [1, 2]})
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown book"

def test_predictions_empty_sentences(client, session):
    job_id = "pred_empty_sentences"
    book = Book(name="b.epub", job_id=job_id, browser_id=VALID_SID, status="done")
    session.add(book)
    session.commit()

    response = client.post(f"/predictions/{job_id}", json={"sentence_ids": []})
    assert response.status_code == 404
    assert response.json()["detail"] == "Empty list"

def test_predictions_success(client, session, sample_vad_json, temp_data_dir):
    job_id = "pred_success_job"
    book = Book(name="b.epub", job_id=job_id, browser_id=VALID_SID, status="done")
    session.add(book)
    session.commit()

    # Create vad.json
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / "vad.json").write_text(json.dumps(sample_vad_json))

    response = client.post(f"/predictions/{job_id}", json={"sentence_ids": [1, 2]})
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["label"] == "joy"
    assert data["certainty"] == 1.0
    assert data["margin"] == 1.0
