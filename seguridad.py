"""Acceso del administrador: inicio de sesión con usuario y contraseña, y sesiones con token."""
import os
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

USUARIO_ADMIN = os.environ.get("ADMIN_USUARIO", "admin")
CLAVE_ADMIN = os.environ.get("ADMIN_CLAVE", "admin2026")
DURACION_SESION = 8 * 3600  # segundos
MAX_INTENTOS = 5            # intentos fallidos permitidos...
VENTANA_INTENTOS = 60       # ...por origen cada este número de segundos

if "ADMIN_CLAVE" not in os.environ:
    print("AVISO: se usa la contraseña de administrador por defecto. Cámbiala con la variable ADMIN_CLAVE.")

router = APIRouter(prefix="/auth", tags=["Acceso"])
esquema = HTTPBearer(auto_error=False)

# Sesiones activas en memoria: token -> momento en que expira. Se pierden al reiniciar el servidor.
SESIONES = {}
INTENTOS_FALLIDOS = {}


class LoginEntrada(BaseModel):
    usuario: str = Field(max_length=60)
    clave: str = Field(max_length=100)


def _iguales(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())


def _limpiar_sesiones():
    ahora = time.time()
    for token in [t for t, expira in SESIONES.items() if expira < ahora]:
        del SESIONES[token]


def requerir_admin(credenciales: HTTPAuthorizationCredentials | None = Depends(esquema)):
    """Dependencia para proteger rutas: exige un token de administrador vigente."""
    token = credenciales.credentials if credenciales else None
    expira = SESIONES.get(token) if token else None
    if expira is None or expira < time.time():
        SESIONES.pop(token, None)
        raise HTTPException(
            status_code=401,
            detail="Sesión no válida o expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post("/login")
def iniciar_sesion(datos: LoginEntrada, peticion: Request):
    origen = peticion.client.host if peticion.client else "desconocido"
    ahora = time.time()
    intentos = [t for t in INTENTOS_FALLIDOS.get(origen, []) if ahora - t < VENTANA_INTENTOS]
    if len(intentos) >= MAX_INTENTOS:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera un minuto e inténtalo de nuevo.")
    usuario_correcto = _iguales(datos.usuario, USUARIO_ADMIN)
    clave_correcta = _iguales(datos.clave, CLAVE_ADMIN)
    if not (usuario_correcto and clave_correcta):
        intentos.append(ahora)
        INTENTOS_FALLIDOS[origen] = intentos
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    INTENTOS_FALLIDOS.pop(origen, None)
    _limpiar_sesiones()
    token = secrets.token_urlsafe(32)
    SESIONES[token] = ahora + DURACION_SESION
    return {"token": token, "expira_en": DURACION_SESION}


@router.post("/salir")
def cerrar_sesion(token: str = Depends(requerir_admin)):
    SESIONES.pop(token, None)
    return {"mensaje": "Sesión cerrada"}


@router.get("/yo")
def sesion_actual(token: str = Depends(requerir_admin)):
    return {"usuario": USUARIO_ADMIN}