from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_login_success():
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["username"] == "user"


def test_login_wrong_password():
    r = client.post("/api/auth/login", json={"username": "user", "password": "wrong"})
    assert r.status_code == 401


def test_login_wrong_username():
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "password"})
    assert r.status_code == 401


def test_me_with_valid_token():
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    token = r.json()["token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "user"


def test_me_without_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 422 or r.status_code == 401


def test_me_with_invalid_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
