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
