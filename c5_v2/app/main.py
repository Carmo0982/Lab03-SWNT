"""API FastAPI del Motor de diagnóstico (C5)."""
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import Diagnostico, SolicitudDiagnostico
from .repository import HistorialRepository, PerfilRepository
from .security import usuario_actual
from .service import MotorDiagnostico, PerfilNoEncontrado, RolNoReconocido

app = FastAPI(title="C5 - Motor de diagnóstico de exposición a IA", version="2.0")

perfiles = PerfilRepository()
historial = HistorialRepository()
motor = MotorDiagnostico(perfiles, historial)

# Traducción de los errores de validación más comunes de Pydantic
MENSAJES = {
    "missing": "Este campo es obligatorio.",
    "less_than_equal": "Debe ser menor o igual a {le}.",
    "greater_than_equal": "Debe ser mayor o igual a {ge}.",
    "string_too_short": "Debe tener al menos {min_length} caracteres.",
    "string_too_long": "Debe tener como máximo {max_length} caracteres.",
    "too_short": "Debe tener al menos {min_length} elemento(s).",
    "too_long": "Debe tener como máximo {max_length} elementos.",
    "float_parsing": "Debe ser un número.",
    "json_invalid": "El cuerpo no es un JSON válido.",
}


@app.exception_handler(RequestValidationError)
async def errores_en_espanol(_: Request, exc: RequestValidationError):
    errores = []
    for e in exc.errors():
        campo = ".".join(str(p) for p in e["loc"] if p != "body") or "cuerpo"
        if e["type"] == "value_error":  # mensajes propios, ya en español
            mensaje = str(e["ctx"]["error"])
        else:
            plantilla = MENSAJES.get(e["type"], "Valor inválido.")
            # 100.0 -> "100" para que el mensaje se lea natural
            ctx = {k: f"{v:g}" if isinstance(v, float) else v
                   for k, v in e.get("ctx", {}).items()}
            mensaje = plantilla.format(**ctx)
        errores.append({"campo": campo, "mensaje": mensaje})
    return JSONResponse(status_code=422, content={"detail": "Datos inválidos", "errores": errores})


@app.post("/diagnosticos", response_model=Diagnostico)
def crear_diagnostico(solicitud: SolicitudDiagnostico, usuario_id: str = Depends(usuario_actual)):
    try:
        return motor.diagnosticar(usuario_id, solicitud.tareas)
    except PerfilNoEncontrado:
        raise HTTPException(status_code=404, detail="No existe un perfil para este usuario.")
    except RolNoReconocido as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/diagnosticos/{usuario_id}", response_model=List[Diagnostico])
def listar_historial(usuario_id: str, autenticado: str = Depends(usuario_actual)):
    if usuario_id != autenticado:
        raise HTTPException(status_code=403, detail="No puedes ver diagnósticos de otro usuario.")
    return historial.listar(usuario_id)
