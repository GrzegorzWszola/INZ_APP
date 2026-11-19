import os
import sys
from unittest.mock import MagicMock
import pytest

# Ensure dummy MODEL_PATH exists before any module imports
if not os.getenv("MODEL_PATH"):
    os.environ["MODEL_PATH"] = "/tmp/dummy_model"

# Mock torch and transformers if not installed in current environment
for mod in ["torch", "transformers"]:
    if mod not in sys.modules:
        try:
            __import__(mod)
        except ImportError:
            sys.modules[mod] = MagicMock()

from src.app.nlp.vad_predictor import VADPredictor

# Patch load_model to avoid attempting to load real weights during testing
def mock_load_model(self, input_path):
    self.device = "cpu"
    self.model_name = getattr(input_path, "name", "dummy_model")
    self.model = MagicMock()
    self.tokenizer = MagicMock()

VADPredictor.load_model = mock_load_model

from fastapi.testclient import TestClient
from src.app.main import app

@pytest.fixture(name="client")
def client_fixture():
    with TestClient(app) as client:
        yield client

@pytest.fixture(name="sample_book_data")
def sample_book_data_fixture():
    return {
        "chapters": [
            {
                "paragraphs": [
                    {
                        "sentences": [
                            {"id": 1, "text": "It was a bright sunny morning."},
                            {"id": 2, "text": "The wind started to howl with anger."},
                            {"id": 3, "text": "She felt peaceful and at ease."}
                        ]
                    }
                ]
            }
        ]
    }
