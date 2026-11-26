import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database.conexion import obtener_bd
from app.reglas import semestres_ofertados

router = APIRouter(tags=["Consultas"])

ORDEN_DIAS = "CASE h.dia_semana WHEN 'LUNES' THEN 1 WHEN 'MARTES' THEN 2 WHEN 'MIERCOLES' THEN 3 WHEN 'JUEVES' THEN 4 WHEN 'VIERNES' THEN 5 ELSE 6 END"


def periodo_activo_o_error(bd: sqlite3.Connection):
    periodo = bd.execute("SELECT * FROM periodos_escolares WHERE activo = 1").fetchone()
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay un periodo escolar activo")
    return periodo


def validar_semestre(periodo, semestre: int):
    if semestre not in semestres_ofertados(periodo["tipo"]):
        raise HTTPException(
            status_code=400,
            detail=f"El semestre {semestre} no se oferta en el periodo {periodo['tipo']}",
        )


@router.get("/grupos")
def listar_grupos(semestre: int | None = None, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Grupos del periodo activo. Solo semestres ofertados."""
    periodo = periodo_activo_o_error(bd)
    if semestre is not None:
        validar_semestre(periodo, semestre)
    filas = bd.execute(
        """SELECT g.id, g.clave, s.numero AS semestre, g.turno, g.cupo, g.estado
           FROM grupos g JOIN semestres s ON s.id = g.semestre_id
           WHERE g.periodo_id = ? AND g.estado != 'INACTIVO'
             AND (? IS NULL OR s.numero = ?)
           ORDER BY s.numero, g.clave""",
        (periodo["id"], semestre, semestre),
    ).fetchall()
    return [dict(f) for f in filas]


@router.get("/grupos/{clave}/materias")
def materias_del_grupo(clave: str, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Materias, profesor y horarios de un grupo (ej. V3) en el periodo activo."""
    periodo = periodo_activo_o_error(bd)
    grupo = bd.execute(
        "SELECT id FROM grupos WHERE periodo_id = ? AND clave = ?",
        (periodo["id"], clave.upper()),
    ).fetchone()
    if not grupo:
        raise HTTPException(status_code=404, detail=f"El grupo {clave.upper()} no se oferta en el periodo activo")
    asignaciones = bd.execute(
        """SELECT a.id, m.nombre AS materia, p.nombre AS profesor
           FROM asignaciones a
           JOIN materias m ON m.id = a.materia_id
           JOIN profesores p ON p.id = a.profesor_id
           WHERE a.grupo_id = ? ORDER BY m.nombre""",
        (grupo["id"],),
    ).fetchall()
    resultado = []
    for a in asignaciones:
        horarios = bd.execute(
            f"""SELECT h.dia_semana AS dia, h.hora_inicio, h.hora_fin, h.salon
                FROM horarios h WHERE h.asignacion_id = ?
                ORDER BY {ORDEN_DIAS}, h.hora_inicio""",
            (a["id"],),
        ).fetchall()
        resultado.append({"materia": a["materia"], "profesor": a["profesor"],
                          "horarios": [dict(h) for h in horarios]})
    return {"grupo": clave.upper(), "materias": resultado}


@router.get("/grupos/{clave}/horario")
def horario_del_grupo(clave: str, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Horario completo del grupo, ordenado por día y hora."""
    periodo = periodo_activo_o_error(bd)
    filas = bd.execute(
        f"""SELECT h.dia_semana AS dia, h.hora_inicio, h.hora_fin, h.salon,
                   m.nombre AS materia, p.nombre AS profesor
            FROM horarios h
            JOIN asignaciones a ON a.id = h.asignacion_id
            JOIN grupos g ON g.id = a.grupo_id
            JOIN materias m ON m.id = a.materia_id
            JOIN profesores p ON p.id = a.profesor_id
            WHERE g.periodo_id = ? AND g.clave = ?
            ORDER BY {ORDEN_DIAS}, h.hora_inicio""",
        (periodo["id"], clave.upper()),
    ).fetchall()
    if not filas:
        raise HTTPException(status_code=404, detail=f"No hay horario para el grupo {clave.upper()} en el periodo activo")
    return {"grupo": clave.upper(), "horario": [dict(f) for f in filas]}


@router.get("/materias")
def listar_materias(semestre: int | None = None, bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        """SELECT m.id, m.nombre, s.numero AS semestre
           FROM materias m JOIN semestres s ON s.id = m.semestre_id
           WHERE (? IS NULL OR s.numero = ?)
           ORDER BY s.numero, m.nombre""",
        (semestre, semestre),
    ).fetchall()
    return [dict(f) for f in filas]


@router.get("/materias/buscar")
def buscar_materia(nombre: str, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Profesores y grupos de una materia en el periodo activo (búsqueda parcial por nombre)."""
    periodo = periodo_activo_o_error(bd)
    filas = bd.execute(
        """SELECT m.nombre AS materia, s.numero AS semestre, g.clave AS grupo, p.nombre AS profesor
           FROM asignaciones a
           JOIN materias m ON m.id = a.materia_id
           JOIN semestres s ON s.id = m.semestre_id
           JOIN grupos g ON g.id = a.grupo_id
           JOIN profesores p ON p.id = a.profesor_id
           WHERE g.periodo_id = ? AND m.nombre LIKE ?
           ORDER BY m.nombre, g.clave""",
        (periodo["id"], f"%{nombre}%"),
    ).fetchall()
    return [dict(f) for f in filas]


@router.get("/profesores")
def listar_profesores(bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute("SELECT id, nombre FROM profesores WHERE activo = 1 ORDER BY nombre").fetchall()
    return [dict(f) for f in filas]


@router.get("/profesores/{profesor_id}/materias")
def materias_del_profesor(profesor_id: int, bd: sqlite3.Connection = Depends(obtener_bd)):
    periodo = periodo_activo_o_error(bd)
    profesor = bd.execute("SELECT id, nombre FROM profesores WHERE id = ?", (profesor_id,)).fetchone()
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    filas = bd.execute(
        """SELECT m.nombre AS materia, s.numero AS semestre, g.clave AS grupo
           FROM asignaciones a
           JOIN materias m ON m.id = a.materia_id
           JOIN semestres s ON s.id = m.semestre_id
           JOIN grupos g ON g.id = a.grupo_id
           WHERE a.profesor_id = ? AND g.periodo_id = ?
           ORDER BY s.numero, m.nombre, g.clave""",
        (profesor_id, periodo["id"]),
    ).fetchall()
    return {"profesor": profesor["nombre"], "materias": [dict(f) for f in filas]}
@router.get("/materias/{materia_id}/profesores")
def profesores_de_la_materia(materia_id: int, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Profesores que imparten una materia. Se usa en el formulario de opiniones."""
    if not bd.execute("SELECT 1 FROM materias WHERE id = ?", (materia_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    filas = bd.execute(
        """SELECT DISTINCT p.id, p.nombre
           FROM asignaciones a JOIN profesores p ON p.id = a.profesor_id
           WHERE a.materia_id = ? AND p.activo = 1 ORDER BY p.nombre""",
        (materia_id,),
    ).fetchall()
    return [dict(f) for f in filas]
