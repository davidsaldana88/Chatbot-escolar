import re
import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database.conexion import obtener_bd
from app.reglas import semestres_ofertados

router = APIRouter(prefix="/admin", tags=["Administración"])

DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
PATRON_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
ORDEN_DIAS = ("CASE h.dia_semana WHEN 'LUNES' THEN 1 WHEN 'MARTES' THEN 2 WHEN 'MIERCOLES' THEN 3 "
              "WHEN 'JUEVES' THEN 4 WHEN 'VIERNES' THEN 5 ELSE 6 END")


# ---------- modelos ----------
class GrupoNuevo(BaseModel):
    periodo_id: int
    semestre: int = Field(ge=1, le=10)
    clave: str = Field(min_length=2, max_length=4)
    turno: Literal["MATUTINO", "VESPERTINO"]
    cupo: int = Field(default=30, ge=0, le=200)


class GrupoCambios(BaseModel):
    turno: Literal["MATUTINO", "VESPERTINO"] | None = None
    cupo: int | None = Field(default=None, ge=0, le=200)
    estado: Literal["DISPONIBLE", "LLENO", "INACTIVO"] | None = None


class MateriaNueva(BaseModel):
    semestre: int = Field(ge=1, le=10)
    nombre: str = Field(min_length=3, max_length=120)
    clave: str | None = Field(default=None, max_length=20)
    descripcion: str | None = Field(default=None, max_length=300)


class MateriaCambios(BaseModel):
    semestre: int | None = Field(default=None, ge=1, le=10)
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    clave: str | None = Field(default=None, max_length=20)
    descripcion: str | None = Field(default=None, max_length=300)


class ProfesorNuevo(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    correo: str | None = Field(default=None, max_length=120)
    area: str | None = Field(default=None, max_length=80)


class ProfesorCambios(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    correo: str | None = Field(default=None, max_length=120)
    area: str | None = Field(default=None, max_length=80)
    activo: bool | None = None


class AsignacionNueva(BaseModel):
    grupo_id: int
    materia_id: int
    profesor_id: int


class AsignacionCambios(BaseModel):
    profesor_id: int


class HorarioNuevo(BaseModel):
    asignacion_id: int
    dia_semana: Literal["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
    hora_inicio: str
    hora_fin: str
    salon: str = Field(min_length=2, max_length=10)


class HorarioCambios(BaseModel):
    dia_semana: Literal["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"] | None = None
    hora_inicio: str | None = None
    hora_fin: str | None = None
    salon: str | None = Field(default=None, min_length=2, max_length=10)


# ---------- utilidades ----------
def error(codigo, detalle):
    raise HTTPException(status_code=codigo, detail=detalle)


def actualizar(bd, tabla, id_, cambios: dict):
    cambios = {k: v for k, v in cambios.items() if v is not None}
    if not cambios:
        error(400, "No se envió ningún cambio")
    columnas = ", ".join(f"{c} = ?" for c in cambios)
    cur = bd.execute(f"UPDATE {tabla} SET {columnas} WHERE id = ?", (*cambios.values(), id_))
    if cur.rowcount == 0:
        error(404, "Registro no encontrado")


def id_semestre(bd, numero):
    fila = bd.execute("SELECT id FROM semestres WHERE numero = ?", (numero,)).fetchone()
    if not fila:
        error(400, f"El semestre {numero} no existe")
    return fila["id"]


def validar_horas(inicio, fin):
    if not (PATRON_HORA.match(inicio) and PATRON_HORA.match(fin)):
        error(400, "Las horas deben tener formato HH:MM, por ejemplo 07:00")
    if inicio >= fin:
        error(400, "La hora de inicio debe ser menor que la hora de fin")


def buscar_choques(bd, asignacion_id, dia, inicio, fin, salon, excluir_id=None):
    """Devuelve la lista de choques (profesor, grupo, salón) del bloque propuesto."""
    base = bd.execute(
        """SELECT a.grupo_id, a.profesor_id, g.periodo_id FROM asignaciones a
           JOIN grupos g ON g.id = a.grupo_id WHERE a.id = ?""", (asignacion_id,)).fetchone()
    if not base:
        error(404, "Asignación no encontrada")
    choques = []
    otros = bd.execute(
        """SELECT h.id, h.salon, a.grupo_id, a.profesor_id, g.clave, m.nombre AS materia
           FROM horarios h JOIN asignaciones a ON a.id = h.asignacion_id
           JOIN grupos g ON g.id = a.grupo_id JOIN materias m ON m.id = a.materia_id
           WHERE g.periodo_id = ? AND h.dia_semana = ? AND h.hora_inicio < ? AND ? < h.hora_fin
             AND h.id != ?""",
        (base["periodo_id"], dia, fin, inicio, excluir_id or -1)).fetchall()
    for o in otros:
        if o["profesor_id"] == base["profesor_id"]:
            choques.append(f"El profesor ya tiene clase ({o['materia']}, grupo {o['clave']}) en ese horario")
        if o["grupo_id"] == base["grupo_id"]:
            choques.append(f"El grupo ya tiene otra materia ({o['materia']}) en ese horario")
        if o["salon"] == salon:
            choques.append(f"El salón {salon} ya está ocupado por el grupo {o['clave']}")
    return choques


# ---------- catálogos ----------
@router.get("/periodos")
def listar_periodos(bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute("SELECT * FROM periodos_escolares ORDER BY anio DESC, tipo").fetchall()
    return [{**dict(f), "semestres_ofertados": semestres_ofertados(f["tipo"])} for f in filas]


# ---------- grupos ----------
@router.get("/grupos")
def listar_grupos(periodo_id: int | None = None, bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        """SELECT g.id, g.clave, s.numero AS semestre, g.turno, g.cupo, g.estado,
                  g.periodo_id, p.anio, p.tipo AS periodo,
                  (SELECT COUNT(*) FROM asignaciones a WHERE a.grupo_id = g.id) AS materias
           FROM grupos g JOIN semestres s ON s.id = g.semestre_id
           JOIN periodos_escolares p ON p.id = g.periodo_id
           WHERE (? IS NULL OR g.periodo_id = ?)
           ORDER BY p.anio DESC, p.tipo, s.numero, g.clave""", (periodo_id, periodo_id)).fetchall()
    return [dict(f) for f in filas]


@router.post("/grupos", status_code=201)
def crear_grupo(datos: GrupoNuevo, bd: sqlite3.Connection = Depends(obtener_bd)):
    periodo = bd.execute("SELECT * FROM periodos_escolares WHERE id = ?", (datos.periodo_id,)).fetchone()
    if not periodo:
        error(400, "El periodo no existe")
    if datos.semestre not in semestres_ofertados(periodo["tipo"]):
        error(400, f"El semestre {datos.semestre} no se oferta en el periodo {periodo['tipo']}")
    programa = bd.execute("SELECT id FROM programas ORDER BY id LIMIT 1").fetchone()
    try:
        cur = bd.execute(
            """INSERT INTO grupos (programa_id, semestre_id, periodo_id, clave, turno, cupo)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (programa["id"], id_semestre(bd, datos.semestre), datos.periodo_id,
             datos.clave.upper(), datos.turno, datos.cupo))
    except sqlite3.IntegrityError:
        error(409, "Ya existe un grupo con esa clave en ese semestre y periodo")
    bd.commit()
    return {"id": cur.lastrowid}


@router.put("/grupos/{grupo_id}")
def editar_grupo(grupo_id: int, datos: GrupoCambios, bd: sqlite3.Connection = Depends(obtener_bd)):
    actualizar(bd, "grupos", grupo_id, datos.model_dump())
    bd.commit()
    return {"id": grupo_id, "actualizado": True}


# ---------- materias ----------
@router.get("/materias")
def listar_materias(bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        """SELECT m.id, m.clave, m.nombre, m.descripcion, s.numero AS semestre
           FROM materias m JOIN semestres s ON s.id = m.semestre_id
           ORDER BY s.numero, m.nombre""").fetchall()
    return [dict(f) for f in filas]


@router.post("/materias", status_code=201)
def crear_materia(datos: MateriaNueva, bd: sqlite3.Connection = Depends(obtener_bd)):
    programa = bd.execute("SELECT id FROM programas ORDER BY id LIMIT 1").fetchone()
    try:
        cur = bd.execute(
            "INSERT INTO materias (programa_id, semestre_id, clave, nombre, descripcion) VALUES (?, ?, ?, ?, ?)",
            (programa["id"], id_semestre(bd, datos.semestre), datos.clave, datos.nombre.strip(), datos.descripcion))
    except sqlite3.IntegrityError:
        error(409, "Ya existe una materia con esa clave")
    bd.commit()
    return {"id": cur.lastrowid}


@router.put("/materias/{materia_id}")
def editar_materia(materia_id: int, datos: MateriaCambios, bd: sqlite3.Connection = Depends(obtener_bd)):
    cambios = datos.model_dump()
    semestre = cambios.pop("semestre", None)
    if semestre is not None:
        actual = bd.execute(
            "SELECT s.numero FROM materias m JOIN semestres s ON s.id = m.semestre_id WHERE m.id = ?",
            (materia_id,)).fetchone()
        if not actual:
            error(404, "Materia no encontrada")
        if actual["numero"] != semestre:
            if bd.execute("SELECT 1 FROM asignaciones WHERE materia_id = ? LIMIT 1", (materia_id,)).fetchone():
                error(409, "No se puede cambiar el semestre de una materia que ya está asignada a grupos")
            cambios["semestre_id"] = id_semestre(bd, semestre)
    try:
        actualizar(bd, "materias", materia_id, cambios)
    except sqlite3.IntegrityError:
        error(409, "Ya existe una materia con esa clave")
    bd.commit()
    return {"id": materia_id, "actualizado": True}

# ---------- profesores ----------
@router.get("/profesores")
def listar_profesores(bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        """SELECT p.id, p.nombre, p.correo, p.area, p.activo,
                  (SELECT COUNT(DISTINCT a.materia_id) FROM asignaciones a WHERE a.profesor_id = p.id) AS materias
           FROM profesores p ORDER BY p.nombre""").fetchall()
    return [dict(f) for f in filas]


@router.post("/profesores", status_code=201)
def crear_profesor(datos: ProfesorNuevo, bd: sqlite3.Connection = Depends(obtener_bd)):
    cur = bd.execute("INSERT INTO profesores (nombre, correo, area) VALUES (?, ?, ?)",
                     (datos.nombre.strip(), datos.correo, datos.area))
    bd.commit()
    return {"id": cur.lastrowid}


@router.put("/profesores/{profesor_id}")
def editar_profesor(profesor_id: int, datos: ProfesorCambios, bd: sqlite3.Connection = Depends(obtener_bd)):
    cambios = datos.model_dump()
    if cambios.get("activo") is not None:
        cambios["activo"] = 1 if cambios["activo"] else 0
    actualizar(bd, "profesores", profesor_id, cambios)
    bd.commit()
    return {"id": profesor_id, "actualizado": True}


# ---------- asignaciones ----------
@router.get("/grupos/{grupo_id}/asignaciones")
def asignaciones_del_grupo(grupo_id: int, bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        """SELECT a.id, m.id AS materia_id, m.nombre AS materia, p.id AS profesor_id, p.nombre AS profesor
           FROM asignaciones a JOIN materias m ON m.id = a.materia_id
           JOIN profesores p ON p.id = a.profesor_id
           WHERE a.grupo_id = ? ORDER BY m.nombre""", (grupo_id,)).fetchall()
    resultado = []
    for a in filas:
        horarios = bd.execute(
            f"""SELECT h.id, h.dia_semana, h.hora_inicio, h.hora_fin, h.salon FROM horarios h
                WHERE h.asignacion_id = ? ORDER BY {ORDEN_DIAS}, h.hora_inicio""", (a["id"],)).fetchall()
        resultado.append({**dict(a), "horarios": [dict(h) for h in horarios]})
    return resultado


@router.post("/asignaciones", status_code=201)
def crear_asignacion(datos: AsignacionNueva, bd: sqlite3.Connection = Depends(obtener_bd)):
    grupo = bd.execute("SELECT s.numero FROM grupos g JOIN semestres s ON s.id = g.semestre_id WHERE g.id = ?",
                       (datos.grupo_id,)).fetchone()
    materia = bd.execute("SELECT s.numero FROM materias m JOIN semestres s ON s.id = m.semestre_id WHERE m.id = ?",
                         (datos.materia_id,)).fetchone()
    if not grupo or not materia:
        error(400, "El grupo o la materia no existen")
    if grupo["numero"] != materia["numero"]:
        error(400, "La materia no pertenece al semestre de ese grupo")
    if not bd.execute("SELECT 1 FROM profesores WHERE id = ? AND activo = 1", (datos.profesor_id,)).fetchone():
        error(400, "El profesor no existe o está inactivo")
    try:
        cur = bd.execute("INSERT INTO asignaciones (grupo_id, materia_id, profesor_id) VALUES (?, ?, ?)",
                         (datos.grupo_id, datos.materia_id, datos.profesor_id))
    except sqlite3.IntegrityError:
        error(409, "Esa materia ya está asignada a ese grupo")
    bd.commit()
    return {"id": cur.lastrowid}


@router.put("/asignaciones/{asignacion_id}")
def cambiar_profesor(asignacion_id: int, datos: AsignacionCambios, bd: sqlite3.Connection = Depends(obtener_bd)):
    """Cambia el profesor de una materia en un grupo, verificando que no genere choques."""
    if not bd.execute("SELECT 1 FROM profesores WHERE id = ? AND activo = 1", (datos.profesor_id,)).fetchone():
        error(400, "El profesor no existe o está inactivo")
    bloques = bd.execute("SELECT * FROM horarios WHERE asignacion_id = ?", (asignacion_id,)).fetchall()
    if not bd.execute("SELECT 1 FROM asignaciones WHERE id = ?", (asignacion_id,)).fetchone():
        error(404, "Asignación no encontrada")
    grupo_periodo = bd.execute(
        "SELECT g.periodo_id FROM asignaciones a JOIN grupos g ON g.id = a.grupo_id WHERE a.id = ?",
        (asignacion_id,)).fetchone()["periodo_id"]
    problemas = []
    for b in bloques:
        ocupado = bd.execute(
            """SELECT g.clave FROM horarios h JOIN asignaciones a ON a.id = h.asignacion_id
               JOIN grupos g ON g.id = a.grupo_id
               WHERE a.profesor_id = ? AND g.periodo_id = ? AND h.dia_semana = ?
                 AND h.hora_inicio < ? AND ? < h.hora_fin AND a.id != ?""",
            (datos.profesor_id, grupo_periodo, b["dia_semana"], b["hora_fin"], b["hora_inicio"],
             asignacion_id)).fetchone()
        if ocupado:
            problemas.append(f"{b['dia_semana']} {b['hora_inicio']}-{b['hora_fin']} choca con el grupo {ocupado['clave']}")
    if problemas:
        error(409, "El profesor tiene choques: " + "; ".join(problemas))
    bd.execute("UPDATE asignaciones SET profesor_id = ? WHERE id = ?", (datos.profesor_id, asignacion_id))
    bd.commit()
    return {"id": asignacion_id, "profesor_id": datos.profesor_id}


# ---------- horarios ----------
@router.post("/horarios", status_code=201)
def crear_horario(datos: HorarioNuevo, bd: sqlite3.Connection = Depends(obtener_bd)):
    validar_horas(datos.hora_inicio, datos.hora_fin)
    salon = datos.salon.upper()
    choques = buscar_choques(bd, datos.asignacion_id, datos.dia_semana, datos.hora_inicio, datos.hora_fin, salon)
    if choques:
        error(409, "; ".join(choques))
    cur = bd.execute(
        "INSERT INTO horarios (asignacion_id, dia_semana, hora_inicio, hora_fin, salon) VALUES (?, ?, ?, ?, ?)",
        (datos.asignacion_id, datos.dia_semana, datos.hora_inicio, datos.hora_fin, salon))
    bd.commit()
    return {"id": cur.lastrowid}


@router.put("/horarios/{horario_id}")
def editar_horario(horario_id: int, datos: HorarioCambios, bd: sqlite3.Connection = Depends(obtener_bd)):
    actual = bd.execute("SELECT * FROM horarios WHERE id = ?", (horario_id,)).fetchone()
    if not actual:
        error(404, "Horario no encontrado")
    cambios = datos.model_dump()
    nuevo = {c: (cambios.get(c) if cambios.get(c) is not None else actual[c])
             for c in ("dia_semana", "hora_inicio", "hora_fin", "salon")}
    nuevo["salon"] = nuevo["salon"].upper()
    validar_horas(nuevo["hora_inicio"], nuevo["hora_fin"])
    choques = buscar_choques(bd, actual["asignacion_id"], nuevo["dia_semana"], nuevo["hora_inicio"],
                             nuevo["hora_fin"], nuevo["salon"], excluir_id=horario_id)
    if choques:
        error(409, "; ".join(choques))
    bd.execute("UPDATE horarios SET dia_semana = ?, hora_inicio = ?, hora_fin = ?, salon = ? WHERE id = ?",
               (nuevo["dia_semana"], nuevo["hora_inicio"], nuevo["hora_fin"], nuevo["salon"], horario_id))
    bd.commit()
    return {"id": horario_id, **nuevo}


@router.delete("/horarios/{horario_id}")
def borrar_horario(horario_id: int, bd: sqlite3.Connection = Depends(obtener_bd)):
    cur = bd.execute("DELETE FROM horarios WHERE id = ?", (horario_id,))
    if cur.rowcount == 0:
        error(404, "Horario no encontrado")
    bd.commit()
    return {"id": horario_id, "eliminado": True}


# ---------- estadísticas del dashboard ----------
@router.get("/estadisticas")
def estadisticas(bd: sqlite3.Connection = Depends(obtener_bd)):
    def uno(sql):
        return bd.execute(sql).fetchone()[0]
    periodo = bd.execute("SELECT id, anio, tipo FROM periodos_escolares WHERE activo = 1").fetchone()
    return {
        "periodo_activo": ({**dict(periodo), "semestres_ofertados": semestres_ofertados(periodo["tipo"])}
                           if periodo else None),
        "totales": {
            "grupos_activos": uno("SELECT COUNT(*) FROM grupos g JOIN periodos_escolares p ON p.id = g.periodo_id "
                                  "WHERE p.activo = 1 AND g.estado != 'INACTIVO'"),
            "materias": uno("SELECT COUNT(*) FROM materias"),
            "profesores": uno("SELECT COUNT(*) FROM profesores WHERE activo = 1"),
            "opiniones_publicadas": uno("SELECT COUNT(*) FROM opiniones WHERE estado = 'PUBLICADA'"),
            "opiniones_pendientes": uno("SELECT COUNT(*) FROM opiniones WHERE estado = 'PENDIENTE'"),
            "sesiones_chat": uno("SELECT COUNT(*) FROM sesiones_chat"),
            "mensajes_estudiantes": uno("SELECT COUNT(*) FROM mensajes_chat WHERE remitente = 'ESTUDIANTE'"),
        },
        "consultas_por_intencion": [dict(f) for f in bd.execute(
            """SELECT intencion, COUNT(*) AS total FROM mensajes_chat
               WHERE remitente = 'CHATBOT' AND intencion IS NOT NULL
               GROUP BY intencion ORDER BY total DESC""").fetchall()],
        "preguntas_frecuentes": [dict(f) for f in bd.execute(
            """SELECT LOWER(TRIM(contenido)) AS pregunta, COUNT(*) AS veces FROM mensajes_chat
               WHERE remitente = 'ESTUDIANTE' GROUP BY LOWER(TRIM(contenido))
               ORDER BY veces DESC, MAX(id) DESC LIMIT 5""").fetchall()],
        "mensajes_por_dia": [dict(f) for f in bd.execute(
            """SELECT DATE(fecha_envio) AS dia, COUNT(*) AS total FROM mensajes_chat
               WHERE remitente = 'ESTUDIANTE' GROUP BY DATE(fecha_envio)
               ORDER BY dia DESC LIMIT 7""").fetchall()],
    }