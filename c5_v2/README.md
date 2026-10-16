# C5 - Motor de diagnóstico de exposición a IA (v2)

Servicio FastAPI que calcula el nivel de exposición a la IA del rol de un usuario, mide cuánto de su tiempo va a tareas automatizables y sugiere hasta 3 roles de menor exposición con su brecha de habilidades.

> El catálogo (`app/catalog.py`) contiene **datos de ejemplo**. Antes de usarlo con usuarios reales, cada nivel de exposición debe respaldarse con una fuente verificada.

## Ejecutar

```bash
pip install fastapi uvicorn httpx pytest pyjwt
export C5_JWT_SECRET="un-secreto-de-al-menos-32-caracteres"
uvicorn app.main:app --reload
```

Documentación interactiva: http://localhost:8000/docs

## Generar un token de prueba

```bash
python -c "from app.security import crear_token; print(crear_token('ana'))"
```

Úsalo en el header `Authorization: Bearer <token>`. En producción el token lo emite el Servicio de autenticación (C2).

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/diagnosticos` | Genera un diagnóstico para el usuario del token. Cuerpo: `{"tareas": [{"descripcion": "...", "porcentaje_tiempo": 60}, ...]}` (los porcentajes suman 100). |
| GET | `/diagnosticos/{usuario_id}` | Historial del usuario; 403 si no es el usuario del token. |

## Pruebas

```bash
pytest -v
```
