import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import backend.src.database as db_mod
import backend.src.routers.books as books_mod
import backend.src.routers.predictions as predictions_mod
from backend.src.database import get_session
from backend.src.main import app

VALID_SID = "a" * 32

@pytest.fixture(name="temp_data_dir")
def temp_data_dir_fixture(tmp_path, monkeypatch):
    """Isolate file storage to a temporary directory."""
    test_dir = tmp_path / "data"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(db_mod, "DATA_DIR", test_dir)
    monkeypatch.setattr(books_mod, "DATA_DIR", test_dir)
    return test_dir

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine, monkeypatch):
    monkeypatch.setattr(db_mod, "engine", engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session, temp_data_dir):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={"sid": VALID_SID}) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="unauth_client")
def unauth_client_fixture(session, temp_data_dir):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="sample_vad_json")
def sample_vad_json_fixture():
    return {
        "meta": {
            "config": {
                "centroids": {
                    "joy": [0.8, 0.7],
                    "sadness": [-0.7, -0.6],
                    "tense": [-0.5, 0.8],
                    "calm": [0.6, -0.6]
                },
                "center": [0.0, 0.0],
                "r_neutral": 0.2
            }
        },
        "vad": {
            "1": [0.85, 0.75],
            "2": [0.80, 0.65],
            "3": [0.05, 0.02],
            "4": [-0.75, -0.65]
        }
    }
