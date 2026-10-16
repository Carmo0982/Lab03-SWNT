"""Repositorios en memoria: perfiles (C3) e historial de diagnósticos.

En producción se reemplazan por implementaciones con base de datos que
respeten la misma interfaz (guardar/obtener, agregar/listar).
"""
from typing import Dict, List, Optional

from .models import Diagnostico, Perfil


class PerfilRepository:
    def __init__(self):
        self._perfiles: Dict[str, Perfil] = {}

    def guardar(self, perfil: Perfil) -> None:
        self._perfiles[perfil.usuario_id] = perfil

    def obtener(self, usuario_id: str) -> Optional[Perfil]:
        return self._perfiles.get(usuario_id)


class HistorialRepository:
    """Conserva todos los diagnósticos de cada usuario, del más antiguo al más reciente."""

    def __init__(self):
        self._historial: Dict[str, List[Diagnostico]] = {}

    def agregar(self, diagnostico: Diagnostico) -> None:
        self._historial.setdefault(diagnostico.usuario_id, []).append(diagnostico)

    def listar(self, usuario_id: str) -> List[Diagnostico]:
        return list(self._historial.get(usuario_id, []))
