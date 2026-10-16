"""Catálogo de roles y exposición (C6) en memoria.

Los niveles y fuentes son DATOS DE EJEMPLO para el laboratorio.
"""
from .models import NivelExposicion as N, RolCatalogo

FUENTE_DEMO = "Dato de ejemplo - reemplazar por fuente verificada"

CATALOGO = [
    RolCatalogo(id="soporte_tecnico", nombre="Soporte técnico", nivel=N.ALTA,
                habilidades=["atención al cliente", "resolución de incidentes",
                             "sistemas operativos", "redes básicas", "documentación"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="dev_junior", nombre="Desarrollador de software junior", nivel=N.ALTA,
                habilidades=["python", "javascript", "git", "sql", "pruebas unitarias"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="captura_datos", nombre="Analista de captura de datos", nivel=N.ALTA,
                habilidades=["excel", "digitación", "control de calidad de datos"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="redactor", nombre="Redactor de contenido", nivel=N.ALTA,
                habilidades=["redacción", "seo", "investigación"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="analista_qa", nombre="Analista de QA", nivel=N.MEDIA,
                habilidades=["pruebas unitarias", "pruebas funcionales", "git", "sql",
                             "documentación"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="devops_junior", nombre="Ingeniero DevOps junior", nivel=N.MEDIA,
                habilidades=["git", "linux", "docker", "redes básicas", "python"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="supervisor_ia", nombre="Supervisor de sistemas de IA", nivel=N.BAJA,
                habilidades=["python", "evaluación de modelos", "documentación",
                             "control de calidad de datos", "pensamiento crítico"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="infra_sitio", nombre="Ingeniero de infraestructura en sitio", nivel=N.BAJA,
                habilidades=["redes básicas", "sistemas operativos", "cableado estructurado",
                             "resolución de incidentes"],
                fuente=FUENTE_DEMO),
    RolCatalogo(id="analista_negocio", nombre="Analista de negocio", nivel=N.BAJA,
                habilidades=["sql", "documentación", "comunicación",
                             "levantamiento de requisitos", "excel"],
                fuente=FUENTE_DEMO),
]
