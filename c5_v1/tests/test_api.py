from fastapi.testclient import TestClient

from app.main import app, perfiles
from app.models import Perfil

client = TestClient(app)
perfiles.guardar(Perfil(usuario_id="api1", rol="Soporte técnico", anios_experiencia=2,
                        habilidades=["redes básicas"]))
CUERPO = {"usuario_id": "api1",
          "tareas": [{"descripcion": "Responder tickets", "porcentaje_tiempo": 100}]}


def test_sin_api_key_rechaza():
    assert client.post("/diagnosticos", json=CUERPO).status_code == 422 or \
        client.post("/diagnosticos", json=CUERPO).status_code == 401


def test_con_api_key_responde():
    r = client.post("/diagnosticos", json=CUERPO, headers={"X-API-Key": "dev-key"})
    assert r.status_code == 200
    assert r.json()["nivel_exposicion"] == "Alta"


def test_perfil_inexistente_404():
    r = client.post("/diagnosticos", json={**CUERPO, "usuario_id": "nadie"},
                    headers={"X-API-Key": "dev-key"})
    assert r.status_code == 404
