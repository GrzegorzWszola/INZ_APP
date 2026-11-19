import io
import json
from unittest.mock import MagicMock
import pytest

def test_predict_vad_endpoint_success(client, sample_book_data, monkeypatch):
    from src.app.routers import prediction

    expected_output = {
        "meta": {
            "model_name": "mock_model",
            "columns": ["valence", "arousal", "dominance"],
            "config": {
                "centroids": {"joy": [0.8, 0.6, 0.5]},
                "r_neutral": 0.25,
                "k": [1.0, 1.0, 1.0],
                "center": [0.0, 0.0, 0.0]
            }
        },
        "vad": {
            "1": [0.8, 0.6, 0.5],
            "2": [-0.5, 0.4, 0.1]
        }
    }

    # Mock process_data on the router's model instance
    monkeypatch.setattr(prediction.model, "process_data", lambda data: expected_output)

    payload_bytes = json.dumps(sample_book_data).encode("utf-8")
    response = client.post(
        "/prediction/job_abc123",
        files={"file": ("book.json", io.BytesIO(payload_bytes), "application/json")}
    )

    assert response.status_code == 200
    assert "attachment; filename=\"vad.json\"" in response.headers.get("content-disposition", "")
    assert response.json() == expected_output

def test_predict_vad_endpoint_corrupt_json(client):
    with pytest.raises(json.JSONDecodeError):
        client.post(
            "/prediction/job_corrupt",
            files={"file": ("book.json", io.BytesIO(b"not a valid json"), "application/json")}
        )
