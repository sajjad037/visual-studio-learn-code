import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "CI/CD Demo API"

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_greet():
    r = client.get("/greet/Azure")
    assert r.status_code == 200
    assert r.json()["greeting"] == "Hello, Azure!"
