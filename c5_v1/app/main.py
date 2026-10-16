"""API FastAPI del Motor de diagnóstico (C5)."""
import os
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException

from .models import Diagnostico, SolicitudDiagnostico
from .repository import HistorialRepository, PerfilRepository
from .service import MotorDiagnostico, PerfilNoEncontrado

app = FastAPI(title="C5 - Motor de diagnóstico de exposición a IA")

perfiles = PerfilRepository()
historial = HistorialRepository()
motor = MotorDiagnostico(perfiles, historial)

API_KEY = os.getenv("C5_API_KEY", "dev-key")


def verificar_api_key(x_api_key: str = Header(...)):
    """Solo acepta llamadas autenticadas con la API key del servicio."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")


@app.post("/diagnosticos", response_model=Diagnostico,
          dependencies=[Depends(verificar_api_key)])
def crear_diagnostico(solicitud: SolicitudDiagnostico):
    try:
        return motor.diagnosticar(solicitud.usuario_id, solicitud.tareas)
    except PerfilNoEncontrado:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")


@app.get("/diagnosticos/{usuario_id}", response_model=List[Diagnostico],
         dependencies=[Depends(verificar_api_key)])
def listar_historial(usuario_id: str):
    return historial.listar(usuario_id)
