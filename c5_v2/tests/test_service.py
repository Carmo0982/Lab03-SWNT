"""Pruebas de la lógica: criterios de aceptación (CA) y regresiones (R) de v1."""
import time

import pytest
from pydantic import ValidationError

from app.catalog import CatalogoInvalido, validar_catalogo
from app.models import NivelExposicion, Perfil, RolCatalogo, SolicitudDiagnostico, Tarea
from app.repository import HistorialRepository, PerfilRepository
from app.service import MotorDiagnostico, RolNoReconocido

TAREAS = [Tarea(descripcion="Responder tickets de usuarios", porcentaje_tiempo=60),
          Tarea(descripcion="Instalar equipos en sitio", porcentaje_tiempo=40)]


def motor_con(**perfil) -> MotorDiagnostico:
    datos = {"usuario_id": "u", "anios_experiencia": 1, "habilidades": [], **perfil}
    repo = PerfilRepository()
    repo.guardar(Perfil(**datos))
    return MotorDiagnostico(repo, HistorialRepository())


# --- Criterios de aceptación ----------------------------------------------

def test_ca1_rol_catalogado_nivel_y_sugerencias_en_menos_de_3s():
    motor = motor_con(rol="Soporte técnico", habilidades=["redes básicas", "sistemas operativos"])
    inicio = time.perf_counter()
    d = motor.diagnosticar("u", TAREAS)
    assert time.perf_counter() - inicio < 3
    assert d.nivel_exposicion == NivelExposicion.ALTA and not d.estimado
    assert 1 <= len(d.roles_sugeridos) <= 3
    assert all(isinstance(s.habilidades_faltantes, list) for s in d.roles_sugeridos)


def test_ca2_rol_no_catalogado_estimado_con_referencia():
    d = motor_con(rol="Soporte técnico nivel 1").diagnosticar("u", TAREAS)
    assert d.estimado and d.rol_referencia == "Soporte técnico"
    assert "Soporte técnico" in d.explicacion


def test_ca3_rol_baja_no_sugiere_media_ni_alta():
    d = motor_con(rol="Analista de negocio", habilidades=["sql"]).diagnosticar("u", TAREAS)
    assert all(s.nivel_exposicion == NivelExposicion.BAJA for s in d.roles_sugeridos)


def test_ca4_mismo_perfil_mismas_respuestas_resultado_identico():
    motor = motor_con(rol="Desarrollador de software junior", habilidades=["python", "git"])
    a, b = motor.diagnosticar("u", TAREAS), motor.diagnosticar("u", TAREAS)
    assert a.model_dump(exclude={"fecha"}) == b.model_dump(exclude={"fecha"})


# --- Regresiones de las fallas encontradas en v1 ---------------------------

def test_r1_rol_sin_relacion_se_rechaza():
    with pytest.raises(RolNoReconocido, match="No encontramos un rol parecido a 'Chef'"):
        motor_con(rol="Chef").diagnosticar("u", TAREAS)


def test_r2_alias_se_reconoce_sin_estimar():
    d = motor_con(rol="Técnico de soporte").diagnosticar("u", TAREAS)
    assert not d.estimado and d.nivel_exposicion == NivelExposicion.ALTA


def test_r3_habilidades_sin_tildes_ni_mayusculas():
    motor = motor_con(rol="Soporte técnico")
    rol = next(r for r in motor.catalogo if r.id == "soporte_tecnico")
    pct, faltantes = motor.coincidencia(["ATENCION  al Cliente"], rol)
    assert pct == 20.0 and "atención al cliente" not in faltantes


def test_r4_porcentajes_deben_sumar_100():
    with pytest.raises(ValidationError, match="suman 150"):
        SolicitudDiagnostico(tareas=[Tarea(descripcion="aaa", porcentaje_tiempo=90),
                                     Tarea(descripcion="bbb", porcentaje_tiempo=60)])
    SolicitudDiagnostico(tareas=[Tarea(descripcion="aaa", porcentaje_tiempo=99.5)])  # tolerancia


def test_r5_tareas_cambian_tiempo_automatizable():
    motor = motor_con(rol="Soporte técnico")
    a = motor.diagnosticar("u", [Tarea(descripcion="Responder tickets", porcentaje_tiempo=100)])
    b = motor.diagnosticar("u", [Tarea(descripcion="Instalar cableado", porcentaje_tiempo=100)])
    assert a.tiempo_en_tareas_automatizables == 100 and b.tiempo_en_tareas_automatizables == 0
    assert "100%" in a.explicacion


def test_r5_explicacion_entre_2_y_3_lineas():
    normal = motor_con(rol="Soporte técnico").diagnosticar("u", TAREAS)
    estimado = motor_con(rol="Soporte técnico nivel 1").diagnosticar("u", TAREAS)
    assert len(normal.explicacion.split("\n")) == 2
    assert len(estimado.explicacion.split("\n")) == 3


def test_r6_desempate_prefiere_menor_exposicion():
    d = motor_con(rol="Soporte técnico", habilidades=[]).diagnosticar("u", TAREAS)
    niveles = [s.nivel_exposicion for s in d.roles_sugeridos]
    assert niveles == [NivelExposicion.BAJA] * 3


def test_r8_catalogo_sin_fuente_o_con_ids_repetidos_falla():
    with pytest.raises(ValidationError, match="debe citar su fuente"):
        RolCatalogo(id="x", nombre="X", nivel="Baja", habilidades=["a"], fuente="  ")
    with pytest.raises(ValidationError):
        RolCatalogo(id="x", nombre="X", nivel="Baja", habilidades=[], fuente="F")
    rol = RolCatalogo(id="x", nombre="X", nivel="Baja", habilidades=["a"], fuente="F")
    with pytest.raises(CatalogoInvalido):
        validar_catalogo([rol, rol])


def test_historial_conserva_diagnosticos_anteriores():
    motor = motor_con(rol="Soporte técnico")
    motor.diagnosticar("u", TAREAS)
    motor.diagnosticar("u", TAREAS)
    assert len(motor.historial.listar("u")) == 2


# --- RNF de rendimiento -----------------------------------------------------

def test_rnf_p95_menor_a_3s_en_200_diagnosticos():
    motor = motor_con(rol="Soporte técnico nivel 1", habilidades=["python", "sql"])
    tiempos = []
    for _ in range(200):
        inicio = time.perf_counter()
        motor.diagnosticar("u", TAREAS)
        tiempos.append(time.perf_counter() - inicio)
    p95 = sorted(tiempos)[int(0.95 * len(tiempos)) - 1]
    assert p95 < 3
