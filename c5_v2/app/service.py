"""Lógica del Motor de diagnóstico de exposición a IA (C5)."""
from datetime import datetime, timezone
from typing import List, Tuple

from .catalog import CATALOGO
from .models import ORDEN_NIVEL, Diagnostico, RolCatalogo, RolSugerido, Tarea
from .repository import HistorialRepository, PerfilRepository
from .text import jaccard, normalizar

UMBRAL_SIMILITUD = 0.34
MAX_SUGERENCIAS = 3


class PerfilNoEncontrado(Exception):
    pass


class RolNoReconocido(Exception):
    def __init__(self, rol: str):
        super().__init__(
            f"No encontramos un rol parecido a '{rol}'. Elige tu rol de la lista del catálogo.")


class MotorDiagnostico:
    def __init__(self, perfiles: PerfilRepository, historial: HistorialRepository,
                 catalogo: List[RolCatalogo] = CATALOGO):
        self.perfiles = perfiles
        self.historial = historial
        # Orden fijo por id para que cualquier empate se resuelva igual siempre
        self.catalogo = sorted(catalogo, key=lambda r: r.id)

    # --- Paso 2: buscar el rol ---------------------------------------------
    def buscar_rol(self, nombre_rol: str) -> Tuple[RolCatalogo, bool]:
        """Devuelve (rol del catálogo, estimado)."""
        buscado = normalizar(nombre_rol)
        for rol in self.catalogo:
            if buscado in {normalizar(n) for n in [rol.nombre, *rol.alias]}:
                return rol, False

        mejor, mejor_sim = None, 0.0
        for rol in self.catalogo:  # catálogo ordenado por id: empates -> id menor
            sim = max(jaccard(nombre_rol, n) for n in [rol.nombre, *rol.alias])
            if sim > mejor_sim:
                mejor, mejor_sim = rol, sim
        if mejor is None or mejor_sim < UMBRAL_SIMILITUD:
            raise RolNoReconocido(nombre_rol)
        return mejor, True

    # --- Paso 4: coincidencia de habilidades -------------------------------
    @staticmethod
    def coincidencia(habilidades_usuario: List[str], rol: RolCatalogo) -> Tuple[float, List[str]]:
        """Habilidades del usuario que exige el rol / habilidades que exige el rol."""
        usuario = {normalizar(h) for h in habilidades_usuario}
        faltantes = [h for h in rol.habilidades if normalizar(h) not in usuario]
        total = len(rol.habilidades)
        return round((total - len(faltantes)) / total * 100, 1), faltantes

    # --- Uso del cuestionario ----------------------------------------------
    @staticmethod
    def tiempo_automatizable(tareas: List[Tarea], rol: RolCatalogo) -> float:
        claves = [normalizar(k) for k in rol.tareas_automatizables]
        total = sum(t.porcentaje_tiempo for t in tareas
                    if any(k in normalizar(t.descripcion) for k in claves))
        return round(total, 1)

    @staticmethod
    def explicar(rol: RolCatalogo, tiempo: float, estimado: bool, rol_usuario: str) -> str:
        lineas = [
            f"Tu rol tiene exposición {rol.nivel.value} a la automatización con IA "
            f"(fuente: {rol.fuente}).",
            f"El {tiempo:g}% de tu tiempo se va en tareas que el catálogo marca como "
            f"automatizables para este rol.",
        ]
        if estimado:
            lineas.append(f"Resultado estimado: '{rol_usuario}' no está en el catálogo y se "
                          f"usó '{rol.nombre}' como referencia.")
        return "\n".join(lineas)

    # --- Flujo principal ----------------------------------------------------
    def diagnosticar(self, usuario_id: str, tareas: List[Tarea]) -> Diagnostico:
        perfil = self.perfiles.obtener(usuario_id)
        if perfil is None:
            raise PerfilNoEncontrado(usuario_id)

        rol, estimado = self.buscar_rol(perfil.rol)          # paso 2
        nivel = rol.nivel                                     # paso 3 (desde C6)
        tiempo = self.tiempo_automatizable(tareas, rol)

        sugeridos = []                                        # paso 4
        for r in self.catalogo:
            if ORDEN_NIVEL[r.nivel] < ORDEN_NIVEL[nivel]:
                pct, faltantes = self.coincidencia(perfil.habilidades, r)
                sugeridos.append(RolSugerido(rol=r.nombre, nivel_exposicion=r.nivel,
                                             coincidencia=pct, habilidades_faltantes=faltantes))
        # Mayor coincidencia, luego menor exposición, luego nombre
        sugeridos.sort(key=lambda s: (-s.coincidencia, ORDEN_NIVEL[s.nivel_exposicion], s.rol))

        diagnostico = Diagnostico(                            # paso 5
            usuario_id=usuario_id, rol_evaluado=perfil.rol, nivel_exposicion=nivel,
            explicacion=self.explicar(rol, tiempo, estimado, perfil.rol), estimado=estimado,
            rol_referencia=rol.nombre if estimado else None,
            tiempo_en_tareas_automatizables=tiempo,
            roles_sugeridos=sugeridos[:MAX_SUGERENCIAS], fecha=datetime.now(timezone.utc))
        self.historial.agregar(diagnostico)
        return diagnostico
