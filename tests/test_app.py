from fastapi.testclient import TestClient

from lakerboat.app import create_app
from lakerboat.config import load_config


def test_app_serves_status_and_injected_ui():
    app = create_app(load_config("config/demo.yaml"), autostart=False)
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    status = client.get("/api/status")
    assert status.status_code == 200
    assert "navigation" in status.json()

    html = client.get("/")
    assert html.status_code == 200
    assert 'statusUrl:"/api/status"' in html.text
    assert 'streamUrl:"/stream.mjpg"' in html.text
