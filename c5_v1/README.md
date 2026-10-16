# C5 - Motor de diagnóstico de exposición a IA (v1)

Servicio FastAPI que calcula el nivel de exposición a la IA del rol de un usuario y sugiere hasta 3 roles de menor exposición.

## Ejecutar

```bash
pip install fastapi uvicorn httpx pytest
uvicorn app.main:app --reload
```

Documentación interactiva: http://localhost:8000/docs

## Endpoints

- `POST /diagnosticos` (header `X-API-Key`): genera un diagnóstico.
- `GET /diagnosticos/{usuario_id}` (header `X-API-Key`): historial.

## Pruebas

```bash
pytest -v
```
