"""Repositorios en memoria: perfiles (C3) e historial de diagnósticos."""
from typing import Dict, List

from .models import Diagnostico, Perfil


class PerfilRepository:
    def __init__(self):
        self._perfiles: Dict[str, Perfil] = {}

    def guardar(self, perfil: Perfil) -> None:
        self._perfiles[perfil.usuario_id] = perfil

    def obtener(self, usuario_id: str) -> Perfil | None:
        return self._perfiles.get(usuario_id)


class HistorialRepository:
    def __init__(self):
        self._historial: Dict[str, List[Diagnostico]] = {}

    def agregar(self, diagnostico: Diagnostico) -> None:
        self._historial.setdefault(diagnostico.usuario_id, []).append(diagnostico)

    def listar(self, usuario_id: str) -> List[Diagnostico]:
        return list(self._historial.get(usuario_id, []))
