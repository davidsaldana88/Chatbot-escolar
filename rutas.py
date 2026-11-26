import sqlite3
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.chatbot.motor import responder
from app.database.conexion import obtener_bd

router = APIRouter(tags=["Chatbot"])

# Memoria de conversación: datos recordados por sesión (por ejemplo, el último grupo mencionado).
CONTEXTOS = {}


class MensajeEntrada(BaseModel):
    mensaje: str
    sesion: str | None = None


def obtener_o_crear_sesion(bd: sqlite3.Connection, clave: str | None):
    if clave:
        fila = bd.execute("SELECT id, clave_sesion FROM sesiones_chat WHERE clave_sesion = ?", (clave,)).fetchone()
        if fila:
            return fila["id"], fila["clave_sesion"]
    nueva = uuid.uuid4().hex
    cur = bd.execute("INSERT INTO sesiones_chat (clave_sesion) VALUES (?)", (nueva,))
    return cur.lastrowid, nueva


@router.post("/chat")
def enviar_mensaje(datos: MensajeEntrada, bd: sqlite3.Connection = Depends(obtener_bd)):
    texto = datos.mensaje.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    if len(texto) > 500:
        raise HTTPException(status_code=400, detail="El mensaje es demasiado largo (máximo 500 caracteres)")
    sesion_id, clave = obtener_o_crear_sesion(bd, datos.sesion)
    contexto = CONTEXTOS.setdefault(clave, {})
    resultado = responder(bd, texto, contexto)
    bd.execute(
        "INSERT INTO mensajes_chat (sesion_id, remitente, contenido) VALUES (?, 'ESTUDIANTE', ?)",
        (sesion_id, texto),
    )
    bd.execute(
        "INSERT INTO mensajes_chat (sesion_id, remitente, contenido, intencion) VALUES (?, 'CHATBOT', ?, ?)",
        (sesion_id, resultado["respuesta"], resultado["intencion"]),
    )
    bd.commit()
    return {"sesion": clave, **resultado}


@router.get("/chat/{clave}/historial")
def historial(clave: str, bd: sqlite3.Connection = Depends(obtener_bd)):
    sesion = bd.execute("SELECT id FROM sesiones_chat WHERE clave_sesion = ?", (clave,)).fetchone()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    filas = bd.execute(
        "SELECT remitente, contenido, intencion, fecha_envio FROM mensajes_chat WHERE sesion_id = ? ORDER BY id",
        (sesion["id"],),
    ).fetchall()
    return [dict(f) for f in filas]