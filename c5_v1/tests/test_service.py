from app.models import NivelExposicion, Perfil, Tarea
from app.repository import HistorialRepository, PerfilRepository
from app.service import MotorDiagnostico

TAREAS = [Tarea(descripcion="Responder tickets", porcentaje_tiempo=60),
          Tarea(descripcion="Documentar soluciones", porcentaje_tiempo=40)]


def crear_motor(perfil: Perfil) -> MotorDiagnostico:
    perfiles = PerfilRepository()
    perfiles.guardar(perfil)
    return MotorDiagnostico(perfiles, HistorialRepository())


def test_rol_catalogado_recibe_nivel_y_sugerencias():
    motor = crear_motor(Perfil(usuario_id="u1", rol="Soporte técnico", anios_experiencia=2,
                               habilidades=["redes básicas", "sistemas operativos"]))
    d = motor.diagnosticar("u1", TAREAS)
    assert d.nivel_exposicion == NivelExposicion.ALTA
    assert not d.estimado
    assert 1 <= len(d.roles_sugeridos) <= 3


def test_rol_no_catalogado_se_marca_estimado():
    motor = crear_motor(Perfil(usuario_id="u2", rol="Soporte técnico nivel 1",
                               anios_experiencia=1, habilidades=["excel"]))
    d = motor.diagnosticar("u2", TAREAS)
    assert d.estimado
    assert d.rol_referencia is not None


def test_rol_baja_no_sugiere_roles_mayores():
    motor = crear_motor(Perfil(usuario_id="u3", rol="Analista de negocio", anios_experiencia=3,
                               habilidades=["sql"]))
    d = motor.diagnosticar("u3", TAREAS)
    assert all(s.nivel_exposicion == NivelExposicion.BAJA for s in d.roles_sugeridos)


def test_diagnostico_determinista():
    motor = crear_motor(Perfil(usuario_id="u4", rol="Desarrollador de software junior",
                               anios_experiencia=1, habilidades=["python", "git"]))
    a = motor.diagnosticar("u4", TAREAS)
    b = motor.diagnosticar("u4", TAREAS)
    assert a.model_dump(exclude={"fecha"}) == b.model_dump(exclude={"fecha"})
