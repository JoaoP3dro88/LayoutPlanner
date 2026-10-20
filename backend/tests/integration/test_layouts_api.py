from fastapi.testclient import TestClient

from app.domain.models import Footprint, Instance, Layout, ObjectType, Room
from app.main import app

client = TestClient(app)


def _payload() -> dict:
    layout = Layout(
        room=Room(outline=[(0, 0), (10000, 0), (10000, 6000), (0, 6000)]),
        types=[ObjectType(id="maq", name="Máquina", footprint=Footprint.rect(1200, 800))],
        instances=[Instance(id="a", type_id="maq", x=1000, y=1000)],
    )
    return layout.model_dump(mode="json")


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_validate_ok():
    r = client.post("/api/v1/layouts/validate", json=_payload())
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_validate_detects_collision():
    p = _payload()
    p["instances"].append({"id": "b", "type_id": "maq", "x": 1500, "y": 1000, "rotation": 0, "fixed": False})
    body = client.post("/api/v1/layouts/validate", json=p).json()
    assert body["ok"] is False and body["issues"][0]["code"] == "collision"


def test_unknown_type_is_422():
    p = _payload()
    p["instances"][0]["type_id"] = "nao_existe"
    assert client.post("/api/v1/layouts/validate", json=p).status_code == 422
