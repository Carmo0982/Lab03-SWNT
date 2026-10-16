"""Lógica del Motor de diagnóstico de exposición a IA (C5)."""
import difflib
from datetime import datetime, timezone
from typing import List, Tuple

from .catalog import CATALOGO
from .models import (Diagnostico, NivelExposicion, RolCatalogo, RolSugerido,
                     Tarea)
from .repository import HistorialRepository, PerfilRepository

# Orden de los niveles para comparar exposición
ORDEN = {NivelExposicion.BAJA: 0, NivelExposicion.MEDIA: 1, NivelExposicion.ALTA: 2}


class PerfilNoEncontrado(Exception):
    pass


class MotorDiagnostico:
    def __init__(self, perfiles: PerfilRepository, historial: HistorialRepository,
                 catalogo: List[RolCatalogo] = CATALOGO):
        self.perfiles = perfiles
        self.historial = historial
        self.catalogo = catalogo

    def buscar_rol(self, nombre_rol: str) -> Tuple[RolCatalogo, bool]:
        """Devuelve el rol del catálogo y si fue estimado (rol más parecido)."""
        for rol in self.catalogo:
            if rol.nombre.lower() == nombre_rol.lower():
                return rol, False
        nombres = [r.nombre.lower() for r in self.catalogo]
        parecido = difflib.get_close_matches(nombre_rol.lower(), nombres, n=1, cutoff=0.0)
        rol = next(r for r in self.catalogo if r.nombre.lower() == parecido[0])
        return rol, True

    @staticmethod
    def coincidencia(habilidades_usuario: List[str], rol: RolCatalogo) -> Tuple[float, List[str]]:
        """Coincidencia = habilidades del usuario que exige el rol / habilidades del rol."""
        usuario = {h.lower().strip() for h in habilidades_usuario}
        requeridas = [h.lower() for h in rol.habilidades]
        faltantes = [h for h in requeridas if h not in usuario]
        porcentaje = (len(requeridas) - len(faltantes)) / len(requeridas) * 100
        return round(porcentaje, 1), faltantes

    def diagnosticar(self, usuario_id: str, tareas: List[Tarea]) -> Diagnostico:
        # Paso 2: obtener perfil y buscar rol
        perfil = self.perfiles.obtener(usuario_id)
        if perfil is None:
            raise PerfilNoEncontrado(usuario_id)
        rol, estimado = self.buscar_rol(perfil.rol)

        # Paso 3: nivel de exposición desde el catálogo
        nivel = rol.nivel

        # Paso 4: roles de menor exposición ordenados por coincidencia
        candidatos = []
        for r in self.catalogo:
            if ORDEN[r.nivel] < ORDEN[nivel]:
                pct, faltantes = self.coincidencia(perfil.habilidades, r)
                candidatos.append(RolSugerido(rol=r.nombre, nivel_exposicion=r.nivel,
                                              coincidencia=pct,
                                              habilidades_faltantes=faltantes))
        candidatos.sort(key=lambda c: c.coincidencia, reverse=True)

        explicacion = (f"Tu rol '{rol.nombre}' tiene exposición {nivel.value} a la "
                       f"automatización con IA. Fuente: {rol.fuente}.")

        # Paso 5: guardar y devolver
        diagnostico = Diagnostico(
            usuario_id=usuario_id, rol_evaluado=perfil.rol, nivel_exposicion=nivel,
            explicacion=explicacion, estimado=estimado,
            rol_referencia=rol.nombre if estimado else None,
            roles_sugeridos=candidatos[:3], fecha=datetime.now(timezone.utc))
        self.historial.agregar(diagnostico)
        return diagnostico
