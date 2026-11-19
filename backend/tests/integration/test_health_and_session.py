def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_session_init_creates_cookie_when_missing(unauth_client):
    response = unauth_client.post("/session/init")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "sid" in response.cookies
    assert len(response.cookies["sid"]) >= 32

def test_session_init_preserves_valid_cookie(unauth_client):
    valid_sid = "a" * 32
    unauth_client.cookies.set("sid", valid_sid)
    response = unauth_client.post("/session/init")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # No new Set-Cookie should be set if valid
    assert "set-cookie" not in response.headers or "sid=" not in response.headers.get("set-cookie", "")

def test_session_init_regenerates_when_cookie_is_short(unauth_client):
    short_sid = "short"
    unauth_client.cookies.set("sid", short_sid)
    response = unauth_client.post("/session/init")
    assert response.status_code == 200
    assert "sid" in response.cookies
    assert len(response.cookies["sid"]) >= 32
    assert response.cookies["sid"] != short_sid
