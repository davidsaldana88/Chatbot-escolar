import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database.conexion import obtener_bd
from app.seguridad import requerir_admin

router = APIRouter(tags=["Opiniones"])


class OpinionEntrada(BaseModel):
    materia_id: int
    profesor_id: int
    calificacion: int = Field(ge=1, le=5)
    comentario: str = Field(min_length=5, max_length=500)
    autor_alias: str | None = Field(default=None, max_length=40)


class EstadoEntrada(BaseModel):
    estado: Literal["PUBLICADA", "RECHAZADA", "PENDIENTE"]


@router.put("/opiniones/{opinion_id}/estado", dependencies=[Depends(requerir_admin)])
def registrar_opinion(datos: OpinionEntrada, bd: sqlite3.Connection = Depends(obtener_bd)):
    """El alumno envía su opinión. Queda PENDIENTE hasta que el administrador la publique."""
    comentario = datos.comentario.strip()
    if len(comentario) < 5:
        raise HTTPException(status_code=400, detail="El comentario es demasiado corto")
    impartida = bd.execute(
        "SELECT 1 FROM asignaciones WHERE materia_id = ? AND profesor_id = ? LIMIT 1",
        (datos.materia_id, datos.profesor_id),
    ).fetchone()
    if not impartida:
        raise HTTPException(status_code=400, detail="Ese profesor no imparte esa materia")
    periodo = bd.execute("SELECT id FROM periodos_escolares WHERE activo = 1").fetchone()
    alias = (datos.autor_alias or "").strip() or "Anónimo"
    cur = bd.execute(
        """INSERT INTO opiniones (materia_id, profesor_id, periodo_id, autor_alias, calificacion, comentario)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (datos.materia_id, datos.profesor_id, periodo["id"] if periodo else None,
         alias, datos.calificacion, comentario),
    )
    bd.commit()
    return {"id": cur.lastrowid, "estado": "PENDIENTE",
            "mensaje": "Gracias, tu opinión fue recibida y se publicará cuando sea revisada."}


@router.get("/opiniones")
def listar_opiniones(materia_id: int | None = None, profesor_id: int | None = None,
                     bd: sqlite3.Connection = Depends(obtener_bd)):
    """Opiniones publicadas (las que ve el estudiante)."""
    filas = bd.execute(
        """SELECT o.id, m.nombre AS materia, p.nombre AS profesor, o.calificacion,
                  o.comentario, o.autor_alias, o.fecha_registro
           FROM opiniones o JOIN materias m ON m.id = o.materia_id
           JOIN profesores p ON p.id = o.profesor_id
           WHERE o.estado = 'PUBLICADA'
             AND (? IS NULL OR o.materia_id = ?) AND (? IS NULL OR o.profesor_id = ?)
           ORDER BY o.fecha_registro DESC, o.id DESC""",
        (materia_id, materia_id, profesor_id, profesor_id),
    ).fetchall()
    return [dict(f) for f in filas]


@router.get("/opiniones/resumen")
def resumen_opiniones(bd: sqlite3.Connection = Depends(obtener_bd)):
    """Promedio y número de opiniones publicadas por profesor y materia."""
    filas = bd.execute(
        """SELECT m.nombre AS materia, p.nombre AS profesor,
                  ROUND(AVG(o.calificacion), 2) AS promedio, COUNT(*) AS total
           FROM opiniones o JOIN materias m ON m.id = o.materia_id
           JOIN profesores p ON p.id = o.profesor_id
           WHERE o.estado = 'PUBLICADA'
           GROUP BY o.materia_id, o.profesor_id
           ORDER BY promedio DESC, total DESC""",
    ).fetchall()
    return [dict(f) for f in filas]


@router.get("/opiniones/pendientes")
def opiniones_pendientes(bd: sqlite3.Connection = Depends(obtener_bd)):
    """Cola de moderación para el administrador."""
    filas = bd.execute(
        """SELECT o.id, m.nombre AS materia, p.nombre AS profesor, o.calificacion,
                  o.comentario, o.autor_alias, o.fecha_registro
           FROM opiniones o JOIN materias m ON m.id = o.materia_id
           JOIN profesores p ON p.id = o.profesor_id
           WHERE o.estado = 'PENDIENTE' ORDER BY o.fecha_registro, o.id""",
    ).fetchall()
    return [dict(f) for f in filas]


@router.put("/opiniones/{opinion_id}/estado")
def moderar_opinion(opinion_id: int, datos: EstadoEntrada, bd: sqlite3.Connection = Depends(obtener_bd)):
    """El administrador publica o rechaza una opinión."""
    cur = bd.execute("UPDATE opiniones SET estado = ? WHERE id = ?", (datos.estado, opinion_id))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Opinión no encontrada")
    bd.commit()
    return {"id": opinion_id, "estado": datos.estado}