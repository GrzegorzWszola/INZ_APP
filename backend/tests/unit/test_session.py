import pytest
from fastapi import HTTPException
from backend.src.routers.session import require_sid

def test_require_sid_none():
    with pytest.raises(HTTPException) as exc_info:
        require_sid(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No session"

def test_require_sid_too_short():
    with pytest.raises(HTTPException) as exc_info:
        require_sid("too_short_token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No session"

def test_require_sid_valid():
    valid_sid = "a" * 32
    assert require_sid(valid_sid) == valid_sid

def test_require_sid_longer_than_32():
    valid_sid = "b" * 44
    assert require_sid(valid_sid) == valid_sid
