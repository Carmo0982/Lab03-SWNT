"""Modelos de datos del Motor de diagnóstico (C5)."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class NivelExposicion(str, Enum):
    """Nivel de exposición a la automatización con IA, expresado como texto."""
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class RolCatalogo(BaseModel):
    """Entrada del catálogo de roles y exposición (C6)."""
    id: str
    nombre: str
    nivel: NivelExposicion
    habilidades: List[str]
    fuente: str


class Perfil(BaseModel):
    """Perfil del usuario tal como lo guarda C3."""
    usuario_id: str
    rol: str
    anios_experiencia: int = Field(ge=0)
    habilidades: List[str]


class Tarea(BaseModel):
    """Respuesta del cuestionario C4: una tarea y su porcentaje de tiempo."""
    descripcion: str
    porcentaje_tiempo: float = Field(ge=0, le=100)


class SolicitudDiagnostico(BaseModel):
    usuario_id: str
    tareas: List[Tarea]


class RolSugerido(BaseModel):
    rol: str
    nivel_exposicion: NivelExposicion
    coincidencia: float  # porcentaje 0-100
    habilidades_faltantes: List[str]


class Diagnostico(BaseModel):
    usuario_id: str
    rol_evaluado: str
    nivel_exposicion: NivelExposicion
    explicacion: str
    estimado: bool
    rol_referencia: Optional[str] = None
    roles_sugeridos: List[RolSugerido]
    fecha: datetime
