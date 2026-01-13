from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_status_no_event():
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_status():
    payload = {"sent_ts": 1.0, "caption": "Claro | Parado", "aux": {"x": 1}}
    r = client.post("/ingest", json=payload)
    assert r.status_code == 200

    s = client.get("/status")
    assert s.status_code == 200
    data = s.json()
    assert "last_event" in data
    assert data["last_event"]["caption"] == "Claro | Parado"

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "server_ts" in data
    assert isinstance(data["server_ts"], (int, float))
