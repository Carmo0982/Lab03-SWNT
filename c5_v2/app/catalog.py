"""Catálogo de roles y exposición (C6) en memoria.

Los niveles, alias, tareas y fuentes son DATOS DE EJEMPLO para el laboratorio:
antes de usar el servicio con usuarios reales, cada nivel debe reemplazarse por
un valor respaldado por una fuente verificada.
"""
from typing import List

from .models import NivelExposicion as N, RolCatalogo

FUENTE_DEMO = "Dato de ejemplo - reemplazar por fuente verificada"


class CatalogoInvalido(Exception):
    pass


def validar_catalogo(roles: List[RolCatalogo]) -> List[RolCatalogo]:
    """Falla al arrancar si hay ids repetidos (fuente y habilidades las valida el modelo)."""
    ids = [r.id for r in roles]
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        raise CatalogoInvalido(f"Ids de rol repetidos en el catálogo: {sorted(repetidos)}")
    return roles


CATALOGO = validar_catalogo([
    RolCatalogo(id="soporte_tecnico", nombre="Soporte técnico",
                alias=["técnico de soporte", "mesa de ayuda", "help desk"], nivel=N.ALTA,
                habilidades=["atención al cliente", "resolución de incidentes",
                             "sistemas operativos", "redes básicas", "documentación"],
                tareas_automatizables=["ticket", "restablecer contraseña", "preguntas frecuentes"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="dev_junior", nombre="Desarrollador de software junior",
                alias=["programador junior", "desarrollador junior"], nivel=N.ALTA,
                habilidades=["python", "javascript", "git", "sql", "pruebas unitarias"],
                tareas_automatizables=["código repetitivo", "crud", "pruebas unitarias"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="captura_datos", nombre="Analista de captura de datos",
                alias=["digitador", "auxiliar de datos"], nivel=N.ALTA,
                habilidades=["excel", "digitación", "control de calidad de datos"],
                tareas_automatizables=["digitar", "transcribir", "formularios"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="redactor", nombre="Redactor de contenido",
                alias=["copywriter", "redactor web"], nivel=N.ALTA,
                habilidades=["redacción", "seo", "investigación"],
                tareas_automatizables=["redactar", "resumir", "traducir"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="analista_qa", nombre="Analista de QA",
                alias=["tester", "analista de pruebas"], nivel=N.MEDIA,
                habilidades=["pruebas unitarias", "pruebas funcionales", "git", "sql",
                             "documentación"],
                tareas_automatizables=["casos de prueba", "regresión"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="devops_junior", nombre="Ingeniero DevOps junior",
                alias=["devops junior"], nivel=N.MEDIA,
                habilidades=["git", "linux", "docker", "redes básicas", "python"],
                tareas_automatizables=["scripts", "despliegue"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="supervisor_ia", nombre="Supervisor de sistemas de IA",
                alias=["evaluador de modelos de ia"], nivel=N.BAJA,
                habilidades=["python", "evaluación de modelos", "documentación",
                             "control de calidad de datos", "pensamiento crítico"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="infra_sitio", nombre="Ingeniero de infraestructura en sitio",
                alias=["técnico de infraestructura", "técnico de redes en sitio"], nivel=N.BAJA,
                habilidades=["redes básicas", "sistemas operativos", "cableado estructurado",
                             "resolución de incidentes"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="analista_negocio", nombre="Analista de negocio",
                alias=["business analyst"], nivel=N.BAJA,
                habilidades=["sql", "documentación", "comunicación",
                             "levantamiento de requisitos", "excel"],
                fuente=FUENTE_DEMO),
])
