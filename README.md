# Laboratorio 3 — Implementación de Componentes con Vibe Coding

**Componente:** C5 Motor de diagnóstico de exposición a IA · **Tipo:** Servicio · **Stack:** Python 3.12 + FastAPI + pytest

## Parte A — Selección del componente

Elegí el **C5 Motor de diagnóstico** porque es el primer paso de valor de la app: sin diagnóstico no hay rol destino, ni ruta de reskilling, ni vacantes recomendadas. Además, su lógica es determinista y se puede verificar con pruebas unitarias contra los 4 criterios de aceptación del Laboratorio 2.

La especificación usada es la del Laboratorio 2 (sección "Especificación C5"), copiada en el prompt inicial.

## Parte B — Prompt inicial

```text
Quiero que generes el código de un componente llamado: Motor de diagnóstico de exposición a IA (C5)
Tipo: Servicio
Lenguaje/Framework preferido: Python 3.12 con FastAPI

Especificación del componente:
- Propósito: calcular qué tan expuesto a la automatización con IA está el rol actual del usuario y proponer roles destino de menor exposición con su brecha de habilidades.
- Entradas:
  - Perfil del usuario desde la BD de usuarios (C3): rol, experiencia y habilidades.
  - Respuestas del Cuestionario de diagnóstico (C4): tareas que realiza y porcentaje de tiempo en cada una.
  - Catálogo de roles y exposición (C6).
- Salidas:
  - Nivel de exposición del rol actual: Alta, Media o Baja, con una explicación de 2 a 3 líneas.
  - Hasta 3 roles destino sugeridos, cada uno con porcentaje de coincidencia de habilidades y lista de habilidades faltantes.
  - Registro del diagnóstico en el historial del usuario.
- Reglas de negocio:
  - El nivel de exposición de cada rol se toma del catálogo C6, y cada valor del catálogo debe citar su fuente.
  - Si el rol del usuario no está en el catálogo, se usa el rol más parecido y el resultado se marca como "estimado".
  - Solo se sugieren roles con exposición menor a la del rol actual.
  - Coincidencia = habilidades del usuario que exige el rol ÷ habilidades totales que exige el rol.
  - Los diagnósticos anteriores se conservan en el historial.
- Flujo principal:
  1. C4 envía las respuestas del cuestionario junto con el identificador del usuario.
  2. El servicio obtiene el perfil y busca el rol en el catálogo.
  3. Calcula el nivel de exposición del rol actual.
  4. Calcula la coincidencia con los roles de menor exposición y ordena los 3 mejores.
  5. Guarda el resultado y lo devuelve.
- RNF clave: respuesta en menos de 3 s (p95); solo acepta llamadas autenticadas y el diagnóstico solo lo ve el usuario; cálculo determinista; nivel expresado como texto.
- Criterios de aceptación:
  - Dado un rol que existe en el catálogo, cuando el usuario completa el cuestionario, entonces recibe su nivel y hasta 3 roles sugeridos con habilidades faltantes en menos de 3 s.
  - Dado un rol que no existe en el catálogo, cuando se genera el diagnóstico, entonces el resultado se marca como "estimado" e indica el rol usado como referencia.
  - Dado un rol actual con exposición Baja, cuando se generan sugerencias, entonces no se propone ningún rol con exposición Media o Alta.
  - Dado el mismo perfil y las mismas respuestas, cuando se repite el diagnóstico, entonces el resultado es idéntico.

Requerimientos adicionales para el código:
- Código modular y comentado.
- Buenas prácticas de FastAPI.
- Pruebas unitarias básicas incluidas (pytest).
- Documentación mínima (README corto con instrucciones de ejecución).
```

### Código generado (v1)

Estructura generada: `app/models.py`, `app/catalog.py`, `app/repository.py`, `app/service.py`, `app/main.py`, `tests/test_service.py`, `tests/test_api.py` y `README.md`.

Fragmento principal, `app/service.py` (v1):

```python
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
```

Autenticación generada en `app/main.py` (v1):

```python
API_KEY = os.getenv("C5_API_KEY", "dev-key")


def verificar_api_key(x_api_key: str = Header(...)):
    """Solo acepta llamadas autenticadas con la API key del servicio."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
```

Resultado de las pruebas de v1: **7 de 7 pasan**.

## Parte C — Validación y refinamiento

### Revisión de v1 con la lista de la Parte C

| Pregunta | Resultado en v1 |
| --- | --- |
| ¿Cumple con entradas/salidas? | Parcial. Recibe las tareas del cuestionario pero no las usa; la explicación tiene 1 línea y no 2 a 3. |
| ¿Aplica las reglas de negocio? | Parcial. Siempre encuentra un "rol parecido", aunque no tenga relación; no valida que cada rol del catálogo cite su fuente. |
| ¿Respeta los RNF? | No en seguridad: una API key compartida no garantiza que "el diagnóstico solo lo ve el usuario". Rendimiento y determinismo sí. |
| ¿Incluye pruebas y documentación? | Sí, pero las pruebas solo cubren el caso feliz de cada criterio. |

### Pruebas exploratorias sobre v1

Que los 7 tests pasaran no significaba que el componente cumpliera la especificación. Escribí un script con casos que la especificación exige y que los tests no cubrían (`scripts/probar_v1.py`):

| # | Caso probado | Resultado en v1 | Problema |
| --- | --- | --- | --- |
| 1 | Rol "Chef" (sin relación con el catálogo) | Estimado como "Desarrollador de software junior", exposición Alta | Diagnóstico sin sentido |
| 2 | Rol "Técnico de soporte" | Referencia: "Ingeniero DevOps junior" | Mapea al rol equivocado |
| 3 | Habilidad "Atencion al cliente" sin tilde | Coincidencia 0% | No normaliza tildes |
| 4 | Porcentajes de tiempo que suman 150 | Aceptado | Falta validación |
| 5 | Mismo perfil con tareas distintas | Resultado idéntico | El cuestionario no influye |
| 6 | Un usuario consulta el historial de otro | HTTP 200 con los datos | Viola el RNF de seguridad |
| 7 | Porcentaje de 120 | "Input should be less than or equal to 100" | Mensaje en inglés |
| 8 | Usuario sin habilidades, rol de exposición Alta | Sugiere roles Media antes que Baja (todos al 0%) | Desempate no definido |
| 9 | Rol de catálogo con fuente vacía | Aceptado | Incumple la regla de citar fuente |

### Prompt refinado

```text
Revisé el código que generaste para el componente C5 (Motor de diagnóstico de exposición a IA, Python 3.12 + FastAPI). Las pruebas pasan, pero al probarlo contra la especificación encontré fallas. Corrige el componente con estos cambios y mantén la estructura de módulos (models, catalog, repository, service, main):

1. Normalización de texto. Compara roles y habilidades sin distinguir mayúsculas, tildes ni espacios repetidos ("Atencion al cliente" debe coincidir con "atención al cliente"). Crea una función `normalizar()` y úsala en todas las comparaciones.

2. Búsqueda del rol. Hoy un rol como "Chef" se mapea a "Desarrollador de software junior" y "Técnico de soporte" a "Ingeniero DevOps junior". Cambia la búsqueda así:
   - Cada rol del catálogo tiene una lista de alias. Si el rol normalizado coincide con el nombre o un alias, el resultado NO es estimado.
   - Si no, calcula la similitud de Jaccard entre las palabras del rol del usuario y las de cada nombre o alias, ignorando palabras vacías (de, del, la, el, y, en). Si la mejor similitud es 0.34 o más, usa ese rol y marca el resultado como "estimado".
   - Si ninguna llega a 0.34, responde HTTP 422 con el mensaje "No encontramos un rol parecido a '<rol>'. Elige tu rol de la lista del catálogo."
   - Los empates se resuelven por id del rol en orden alfabético.

3. Uso del cuestionario. Hoy las tareas se reciben pero no cambian nada. Agrega a cada rol del catálogo una lista `tareas_automatizables` (palabras clave). Calcula `tiempo_en_tareas_automatizables` = suma de los porcentajes de las tareas cuya descripción normalizada contiene alguna de esas palabras. Devuélvelo en la salida y menciónalo en la explicación. El nivel de exposición se sigue tomando del catálogo.

4. Validación de entradas, con mensajes en español:
   - Entre 1 y 10 tareas; cada descripción entre 3 y 200 caracteres.
   - Los porcentajes deben sumar 100 (tolerancia de ±1). Si no: "Los porcentajes de tiempo deben sumar 100; suman <total>."
   - Agrega un manejador de `RequestValidationError` que devuelva 422 con el formato `{"detail": "Datos inválidos", "errores": [{"campo": ..., "mensaje": ...}]}` y mensajes en español.

5. Explicación de 2 a 3 líneas (separadas por "\n"): línea 1 con el nivel y la fuente; línea 2 con el tiempo en tareas automatizables; línea 3, solo si es estimado, con el rol usado como referencia.

6. Orden determinista de las sugerencias: primero mayor coincidencia, luego menor exposición (Baja antes que Media) y luego nombre alfabético. Hoy, con coincidencia 0%, se sugieren roles Media antes que roles Baja.

7. Seguridad. La API key compartida permite que cualquiera lea el historial de otro usuario. Reemplázala por JWT Bearer (HS256, librería PyJWT, secreto en la variable de entorno C5_JWT_SECRET):
   - El `usuario_id` se toma del claim `sub` del token, no del cuerpo de la petición.
   - `GET /diagnosticos/{usuario_id}` devuelve 403 "No puedes ver diagnósticos de otro usuario" si `usuario_id` no es igual a `sub`.
   - Token ausente, inválido o vencido: 401 con mensaje en español.

8. Catálogo. Valida al cargar que cada rol tenga fuente no vacía, al menos una habilidad e id único; si no, la aplicación no debe arrancar.

9. Pruebas. Mantén las pruebas de los 4 criterios de aceptación y agrega una prueba por cada falla de esta lista, más una prueba de rendimiento que ejecute 200 diagnósticos y verifique que el percentil 95 es menor a 3 s. Actualiza el README con cómo generar un token de prueba.
```

### Código refinado (v2)

Estructura: se agregan `app/text.py` (normalización y similitud) y `app/security.py` (JWT); el resto de módulos se conserva.

`app/service.py` (v2):

```python
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
```

`app/security.py` (v2):

```python
"""Autenticación JWT Bearer (HS256). El usuario autenticado es el claim `sub`."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITMO = "HS256"
bearer = HTTPBearer(auto_error=False)


def secreto() -> str:
    # HS256 requiere una clave de al menos 32 bytes (RFC 7518, sección 3.2)
    return os.getenv("C5_JWT_SECRET", "solo-para-desarrollo-cambiar-en-produccion")


def crear_token(usuario_id: str, minutos: int = 30) -> str:
    """Genera un token de prueba. En producción lo emite el Servicio de autenticación (C2)."""
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    return jwt.encode({"sub": usuario_id, "exp": exp}, secreto(), algorithm=ALGORITMO)


def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    """Devuelve el usuario_id del token o responde 401."""
    if cred is None:
        raise HTTPException(status_code=401, detail="Falta el token de autenticación.")
    try:
        datos = jwt.decode(cred.credentials, secreto(), algorithms=[ALGORITMO],
                           options={"require": ["sub", "exp"]})
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token venció. Inicia sesión de nuevo.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return datos["sub"]
```

Validación de porcentajes en `app/models.py` (v2):

```python
class SolicitudDiagnostico(BaseModel):
    """Cuerpo de POST /diagnosticos. El usuario se toma del token, no del cuerpo."""
    tareas: List[Tarea] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def porcentajes_suman_100(self):
        total = sum(t.porcentaje_tiempo for t in self.tareas)
        if abs(total - 100) > TOLERANCIA_PORCENTAJE:
            raise ValueError(f"Los porcentajes de tiempo deben sumar 100; suman {total:g}.")
        return self
```

Resultado de las pruebas de v2: **23 de 23 pasan** (4 de criterios de aceptación, 17 de regresión, seguridad y API, 1 de historial y 1 de rendimiento con 200 diagnósticos).

Al levantar el servidor con `uvicorn` y llamarlo por HTTP, una petición sin token devolvió `401 {"detail":"Falta el token de autenticación."}`. En esa prueba, PyJWT advirtió que el secreto usado tenía menos de 32 bytes, el mínimo recomendado para HS256 (RFC 7518, sección 3.2); el valor por defecto de v2 (28 bytes) tenía el mismo problema. Ajusté el secreto por defecto y el README; fue un tercer ajuste pequeño que ninguno de los dos prompts había previsto.

### Mismos casos exploratorios sobre v2

| # | Caso | Resultado en v2 |
| --- | --- | --- |
| 1 | Rol "Chef" | 422: "No encontramos un rol parecido a 'Chef'. Elige tu rol de la lista del catálogo." |
| 2 | Rol "Técnico de soporte" | Reconocido por alias, no estimado, exposición Alta |
| 3 | "Atencion al cliente" | Coincidencia 20% con Soporte técnico (1 de 5 habilidades) |
| 4 | Porcentajes que suman 150 | 422: "Los porcentajes de tiempo deben sumar 100; suman 150." |
| 5 | Tareas distintas | Tiempo en tareas automatizables: 100% frente a 0% |
| 6 | Historial de otro usuario | 403 |
| 7 | Porcentaje de 120 | 422: "Debe ser menor o igual a 100." |
| 8 | Desempate | Los 3 sugeridos son de exposición Baja, en orden alfabético |
| 9 | Fuente vacía | Rechazado: "Cada rol del catálogo debe citar su fuente." |

## Parte D — Validación con criterios de aceptación

| Criterio de aceptación (Lab 2) | v1 | v2 | Evidencia en v2 |
| --- | --- | --- | --- |
| CA1: rol catalogado recibe nivel y hasta 3 roles con habilidades faltantes en menos de 3 s | Cumple | Cumple | `test_ca1_...` y `test_rnf_p95_...` (p95 < 3 s en 200 ejecuciones) |
| CA2: rol no catalogado se marca "estimado" e indica la referencia | Cumple a medias: marca "estimado" pero la referencia puede ser absurda (casos 1 y 2) | Cumple | `test_ca2_...`, `test_r1_...`, `test_r2_...` |
| CA3: rol de exposición Baja no recibe sugerencias Media ni Alta | Cumple | Cumple | `test_ca3_...` |
| CA4: mismo perfil y respuestas, resultado idéntico | Cumple | Cumple, con desempate explícito | `test_ca4_...`, `test_r6_...` |

**Ajustes que quedan pendientes:**

- El catálogo tiene **datos de ejemplo**: los niveles de exposición, alias y tareas automatizables no provienen de una fuente verificada. Antes de usar el servicio con usuarios reales hay que reemplazarlos por datos respaldados.
- La especificación del Laboratorio 2 debe actualizarse con tres decisiones nuevas: el umbral de similitud (0.34) con error si no hay rol parecido, la salida `tiempo_en_tareas_automatizables` y el criterio de desempate.
- Los repositorios están en memoria; falta conectarlos a la BD real de C3 y al historial persistente.

## Reflexión

**¿Qué funcionó bien en el prompt?** Pegar la especificación completa del Laboratorio 2 con la estructura de la plantilla. Con eso, la IA generó desde el primer intento un servicio modular, con los 5 pasos del flujo, los niveles como texto y una prueba por cada criterio de aceptación.

**¿Qué tuve que mejorar?** Todo lo que la especificación dejaba ambiguo, la IA lo resolvió de la forma más simple. "Usar el rol más parecido" terminó en emparejar cualquier texto, "solo lo ve el usuario" en una API key compartida, y las tareas del cuestionario quedaron sin uso porque nadie dijo para qué servían. El prompt refinado tuvo que dar valores concretos: el umbral de similitud, la fórmula del tiempo automatizable, el orden de desempate y la regla de que `sub` debe coincidir con `usuario_id`.

**¿Qué aprendí sobre cómo guiar a la IA para programar?** Que las pruebas que genera la IA confirman lo que ella misma entendió, no lo que pide la especificación: v1 pasaba 7 de 7 tests y aun así tenía 9 fallas. Lo que me permitió encontrarlas fue probar casos límite yo mismo y convertir cada falla en una instrucción medible y en una prueba de regresión. También aprendí que refinar el prompt obliga a mejorar la especificación, no solo el código.
