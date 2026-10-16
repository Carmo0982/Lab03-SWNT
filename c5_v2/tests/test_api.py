"""Pruebas de la API: autenticación, autorización y mensajes en español."""
from fastapi.testclient import TestClient

from app.main import app, perfiles
from app.models import Perfil
from app.security import crear_token

client = TestClient(app)
perfiles.guardar(Perfil(usuario_id="ana", rol="Soporte técnico", anios_experiencia=2,
                        habilidades=["redes básicas"]))
perfiles.guardar(Perfil(usuario_id="luis", rol="Chef", anios_experiencia=1, habilidades=[]))
CUERPO = {"tareas": [{"descripcion": "Responder tickets", "porcentaje_tiempo": 100}]}


def auth(usuario: str, minutos: int = 30) -> dict:
    return {"Authorization": f"Bearer {crear_token(usuario, minutos)}"}


def test_diagnostico_con_token_valido():
    r = client.post("/diagnosticos", json=CUERPO, headers=auth("ana"))
    assert r.status_code == 200
    assert r.json()["usuario_id"] == "ana" and r.json()["nivel_exposicion"] == "Alta"


def test_sin_token_401_en_espanol():
    r = client.post("/diagnosticos", json=CUERPO)
    assert r.status_code == 401 and r.json()["detail"] == "Falta el token de autenticación."


def test_token_vencido_401():
    r = client.post("/diagnosticos", json=CUERPO, headers=auth("ana", minutos=-1))
    assert r.status_code == 401 and "venció" in r.json()["detail"]


def test_token_alterado_401():
    r = client.post("/diagnosticos", json=CUERPO,
                    headers={"Authorization": "Bearer " + crear_token("ana") + "x"})
    assert r.status_code == 401


def test_r7_no_puede_ver_historial_de_otro_usuario():
    client.post("/diagnosticos", json=CUERPO, headers=auth("ana"))
    assert client.get("/diagnosticos/ana", headers=auth("luis")).status_code == 403
    propio = client.get("/diagnosticos/ana", headers=auth("ana"))
    assert propio.status_code == 200 and len(propio.json()) >= 1


def test_r4_errores_de_validacion_en_espanol():
    cuerpo = {"tareas": [{"descripcion": "ab", "porcentaje_tiempo": 120}]}
    r = client.post("/diagnosticos", json=cuerpo, headers=auth("ana"))
    assert r.status_code == 422 and r.json()["detail"] == "Datos inválidos"
    mensajes = {e["mensaje"] for e in r.json()["errores"]}
    assert "Debe tener al menos 3 caracteres." in mensajes
    assert "Debe ser menor o igual a 100." in mensajes


def test_r4_suma_distinta_de_100_en_espanol():
    cuerpo = {"tareas": [{"descripcion": "aaa", "porcentaje_tiempo": 30}]}
    r = client.post("/diagnosticos", json=cuerpo, headers=auth("ana"))
    assert r.status_code == 422
    assert r.json()["errores"][0]["mensaje"] == "Los porcentajes de tiempo deben sumar 100; suman 30."


def test_r1_rol_no_reconocido_422():
    r = client.post("/diagnosticos", json=CUERPO, headers=auth("luis"))
    assert r.status_code == 422 and "Chef" in r.json()["detail"]


def test_perfil_inexistente_404():
    r = client.post("/diagnosticos", json=CUERPO, headers=auth("nadie"))
    assert r.status_code == 404
