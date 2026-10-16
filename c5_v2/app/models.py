"""Modelos de datos del Motor de diagnóstico (C5)."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

TOLERANCIA_PORCENTAJE = 1.0


class NivelExposicion(str, Enum):
    """Nivel de exposición a la automatización con IA, expresado como texto."""
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


# Orden para comparar niveles: menor número = menor exposición
ORDEN_NIVEL = {NivelExposicion.BAJA: 0, NivelExposicion.MEDIA: 1, NivelExposicion.ALTA: 2}


class RolCatalogo(BaseModel):
    """Entrada del catálogo de roles y exposición (C6)."""
    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    alias: List[str] = []
    nivel: NivelExposicion
    habilidades: List[str] = Field(min_length=1)
    tareas_automatizables: List[str] = []
    fuente: str

    @field_validator("fuente")
    @classmethod
    def fuente_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cada rol del catálogo debe citar su fuente.")
        return v


class Perfil(BaseModel):
    """Perfil del usuario tal como lo guarda C3."""
    usuario_id: str
    rol: str
    anios_experiencia: int = Field(ge=0)
    habilidades: List[str]


class Tarea(BaseModel):
    """Respuesta del cuestionario C4: una tarea y su porcentaje de tiempo."""
    descripcion: str = Field(min_length=3, max_length=200)
    porcentaje_tiempo: float = Field(ge=0, le=100)


class SolicitudDiagnostico(BaseModel):
    """Cuerpo de POST /diagnosticos. El usuario se toma del token, no del cuerpo."""
    tareas: List[Tarea] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def porcentajes_suman_100(self):
        total = sum(t.porcentaje_tiempo for t in self.tareas)
        if abs(total - 100) > TOLERANCIA_PORCENTAJE:
            raise ValueError(f"Los porcentajes de tiempo deben sumar 100; suman {total:g}.")
        return self


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
    tiempo_en_tareas_automatizables: float
    roles_sugeridos: List[RolSugerido]
    fecha: datetime
