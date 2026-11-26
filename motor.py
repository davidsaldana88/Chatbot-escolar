"""Motor del chatbot: identifica la intención, extrae datos del mensaje y arma la respuesta."""
import re
import sqlite3

from app.chatbot import pln
from app.reglas import semestres_ofertados

NOMBRES_PERIODO = {"ENERO_JUNIO": "Enero–Junio", "AGOSTO_DICIEMBRE": "Agosto–Diciembre"}
DIAS = {"LUNES": "Lunes", "MARTES": "Martes", "MIERCOLES": "Miércoles",
        "JUEVES": "Jueves", "VIERNES": "Viernes", "SABADO": "Sábado"}
ORDEN_DIAS = ("CASE h.dia_semana WHEN 'LUNES' THEN 1 WHEN 'MARTES' THEN 2 WHEN 'MIERCOLES' THEN 3 "
              "WHEN 'JUEVES' THEN 4 WHEN 'VIERNES' THEN 5 ELSE 6 END")

ORDINALES = {"primero": 1, "primer": 1, "segundo": 2, "tercero": 3, "tercer": 3, "cuarto": 4,
             "quinto": 5, "sexto": 6, "septimo": 7, "octavo": 8, "noveno": 9, "decimo": 10}
ROMANOS = {"1": "i", "2": "ii", "3": "iii"}
TITULOS = {"dr", "en", "sis", "ing", "mec", "tic", "lic", "inv", "edu", "com"}

# Palabras clave de cada intención con su peso.
PALABRAS_INTENCION = {
    "SALUDO": {"hola": 2, "buenas": 2, "buenos": 1, "tardes": 1, "noches": 1, "saludos": 2, "hey": 2},
    "DESPEDIDA": {"adios": 2, "gracias": 2, "chao": 2, "bye": 2},
    "AYUDA": {"ayuda": 3, "ayudar": 2, "opciones": 2, "menu": 2, "comandos": 2, "puedes": 1,
              "funciona": 1, "hacer": 1},
    "PERIODO": {"periodo": 3, "ciclo": 2, "ofertan": 2, "oferta": 2, "ofertados": 2, "vigente": 1,
                "actual": 1, "inscripcion": 1, "inscripciones": 1},
    "GRUPOS": {"grupo": 3, "grupos": 3, "inscribir": 1, "inscribirme": 1, "turno": 1, "cupo": 1,
               "disponible": 1, "disponibles": 1},
    "MATERIAS": {"materia": 3, "materias": 3, "asignatura": 3, "asignaturas": 3, "curso": 2,
                 "cursos": 2, "clases": 2, "cursar": 2, "llevar": 1},
    "PROFESORES": {"profesor": 3, "profesores": 3, "maestro": 3, "maestros": 3, "docente": 3,
                   "docentes": 3, "imparte": 3, "imparten": 3, "impartir": 2, "quien": 2,
                   "quienes": 2, "catedratico": 3},
    "HORARIOS": {"horario": 3, "horarios": 3, "hora": 3, "horas": 3, "salon": 2, "salones": 2,
                 "cuando": 1},
    "OPINIONES": {"opinion": 3, "opiniones": 3, "opinar": 3, "resena": 3, "calificacion": 2,
                  "comentario": 1, "comentarios": 1, "valoracion": 2, "recomiendan": 1},
}
# En caso de empate gana la intención que aparece primero.
PRIORIDAD = ["OPINIONES", "HORARIOS", "PROFESORES", "MATERIAS", "GRUPOS", "PERIODO",
             "AYUDA", "DESPEDIDA", "SALUDO"]


def _raices_intencion():
    resultado = {}
    for intencion, palabras in PALABRAS_INTENCION.items():
        raices = {}
        for palabra, peso in palabras.items():
            r = pln.raiz(palabra)
            raices[r] = max(peso, raices.get(r, 0))
        resultado[intencion] = raices
    return resultado


RAICES_INTENCION = _raices_intencion()

MENU = ["Grupos disponibles", "Materias", "Profesores", "Horarios"]


# ---------- utilidades ----------
def texto_lista(numeros):
    numeros = [str(n) for n in numeros]
    if len(numeros) <= 1:
        return "".join(numeros)
    return ", ".join(numeros[:-1]) + " y " + numeros[-1]


def nombre_turno(turno):
    return (turno or "").capitalize()


def cargar_periodo(bd):
    return bd.execute("SELECT * FROM periodos_escolares WHERE activo = 1").fetchone()


def etiqueta_periodo(periodo):
    return f"{NOMBRES_PERIODO[periodo['tipo']]} {periodo['anio']}"


def grupos_del_periodo(bd, periodo):
    return bd.execute(
        """SELECT g.id, g.clave, g.turno, g.cupo, g.estado, s.numero AS semestre
           FROM grupos g JOIN semestres s ON s.id = g.semestre_id
           WHERE g.periodo_id = ? AND g.estado != 'INACTIVO'
           ORDER BY s.numero, g.clave""",
        (periodo["id"],),
    ).fetchall()


def sin_semestre_ofertado(periodo, semestre):
    ofertados = semestres_ofertados(periodo["tipo"])
    return (f"El semestre {semestre} no se oferta en el periodo {etiqueta_periodo(periodo)}. "
            f"En este periodo se ofertan los semestres {texto_lista(ofertados)}.")


# ---------- extracción de datos del mensaje ----------
def extraer_semestre(texto, tokens):
    m = re.search(r"semestre\s*(\d{1,2})\b", texto) or re.search(r"\b(\d{1,2})\s*(?:o|vo|to|er|ro)?\s*semestre", texto)
    if m and 1 <= int(m.group(1)) <= 10:
        return int(m.group(1))
    if "semestre" in tokens or "grado" in tokens:
        for palabra, numero in ORDINALES.items():
            if palabra in tokens:
                return numero
    return None


def extraer_grupo(texto):
    m = re.search(r"\b([msv])-?(\d{1,2})\b", texto) or None
    if m:
        letra, numero = m.group(1), int(m.group(2))
    else:
        m = re.search(r"\b(\d{1,2})([msv])\b", texto)
        if not m:
            return None
        letra, numero = m.group(2), int(m.group(1))
    return f"{letra.upper()}{numero}" if 1 <= numero <= 10 else None


def extraer_turnos(texto):
    if "matutin" in texto:
        return ["M", "S"]
    if "vespertin" in texto:
        return ["V"]
    return None


def palabras_significativas(nombre):
    return pln.quitar_vacias(pln.tokenizar(pln.normalizar(nombre)))


def construir_vocabulario(materias, profesores):
    vocabulario = set()
    for palabras in PALABRAS_INTENCION.values():
        vocabulario.update(palabras)
    for m in materias:
        vocabulario.update(p for p in palabras_significativas(m["nombre"]) if len(p) >= 4)
    for p in profesores:
        vocabulario.update(nombre_de_persona(p["nombre"]))
    return vocabulario


def nombre_de_persona(nombre):
    """Palabras del nombre sin títulos académicos (Dr., Ing., M. en C., ...)."""
    return [t for t in pln.tokenizar(pln.normalizar(nombre)) if len(t) > 2 and t not in TITULOS]


def buscar_materias(materias, raices_mensaje, tokens):
    """Devuelve (candidatas, parciales). Candidatas: coincidencia fuerte con el nombre."""
    extra = {pln.raiz(ROMANOS[t]) for t in tokens if t in ROMANOS}
    raices = raices_mensaje | extra
    romanas = {"i", "ii", "iii"}
    puntuadas = []
    for m in materias:
        propias = {pln.raiz(p) for p in palabras_significativas(m["nombre"])}
        if not propias:
            continue
        coinciden = propias & raices
        if not (coinciden - romanas):
            continue
        puntuadas.append((len(coinciden) / len(propias), m))
    if not puntuadas:
        return [], []
    mejor = max(p for p, _ in puntuadas)
    if mejor >= 0.6:
        return [m for p, m in puntuadas if p == mejor], []
    puntuadas.sort(key=lambda x: -x[0])
    return [], [m for _, m in puntuadas[:6]]


def buscar_profesores(profesores, tokens):
    puntuados = []
    for p in profesores:
        palabras = set(nombre_de_persona(p["nombre"]))
        coinciden = {t for t in tokens if len(t) >= 4 and t in palabras}
        if coinciden:
            puntuados.append((len(coinciden), p))
    if not puntuados:
        return []
    mejor = max(n for n, _ in puntuados)
    return [p for n, p in puntuados if n == mejor]


# ---------- detección de intención ----------
def detectar_intencion(raices, ent):
    puntajes = {i: sum(peso for r, peso in raices_i.items() if r in raices)
                for i, raices_i in RAICES_INTENCION.items()}
    positivos = {i: p for i, p in puntajes.items() if p > 0}
    if len(positivos) > 1:
        positivos.pop("SALUDO", None)
    if positivos:
        mejor = min(positivos, key=lambda i: (-positivos[i], PRIORIDAD.index(i)))
        # «¿Qué materias da Octavio?»: si nombra a un profesor, la consulta es sobre el profesor.
        if (mejor in {"MATERIAS", "GRUPOS"} and ent["profesores"]
                and not ent["grupo"] and not ent["semestre"]):
            return "PROFESORES"
        return mejor
    if ent["grupo"]:
        return "MATERIAS"
    if ent["materias"] or ent["profesores"] or ent["parciales"]:
        return "PROFESORES"
    if ent["semestre"]:
        return "GRUPOS"
    return "NO_ENTENDIDO"


# ---------- respuestas ----------
def r_saludo():
    return ("¡Hola! Soy el asistente de inscripciones de Ingeniería en Sistemas Inteligentes. "
            "Puedo ayudarte a consultar grupos, materias, profesores y horarios. ¿Qué necesitas?"), MENU


def r_despedida():
    return "¡Con gusto! Si necesitas algo más sobre tu inscripción, aquí estaré.", MENU


def r_ayuda():
    return ("Puedo ayudarte con esto:\n"
            "- Grupos disponibles: «¿Qué grupos hay del semestre 3?»\n"
            "- Materias: «¿Qué materias tiene el grupo V3?»\n"
            "- Profesores: «¿Quién imparte Cálculo III?»\n"
            "- Horarios: «Horario del grupo M5» o «¿A qué hora es Ingeniería de Software?»\n"
            "- Periodo: «¿Qué semestres se ofertan?»"), MENU


def r_periodo(bd, periodo):
    grupos = grupos_del_periodo(bd, periodo)
    ofertados = semestres_ofertados(periodo["tipo"])
    return (f"El periodo activo es {etiqueta_periodo(periodo)}. "
            f"Se ofertan los semestres {texto_lista(ofertados)}, con {len(grupos)} grupos en total."), \
           ["Grupos disponibles", "Materias"]


def r_grupos(bd, periodo, ent):
    ofertados = semestres_ofertados(periodo["tipo"])
    semestre = ent["semestre"]
    if semestre and semestre not in ofertados:
        return sin_semestre_ofertado(periodo, semestre), [f"Grupos del semestre {ofertados[0]}"]
    grupos = grupos_del_periodo(bd, periodo)
    if ent["turnos"]:
        grupos = [g for g in grupos if g["clave"][0] in ent["turnos"]]
    if semestre:
        grupos = [g for g in grupos if g["semestre"] == semestre]
        lineas = [f"- {g['clave']} · {nombre_turno(g['turno'])} · cupo {g['cupo']}" for g in grupos]
        return (f"Grupos del semestre {semestre} ({etiqueta_periodo(periodo)}):\n" + "\n".join(lineas),
                [f"Horario del grupo {g['clave']}" for g in grupos][:3])
    por_semestre = {}
    for g in grupos:
        por_semestre.setdefault(g["semestre"], []).append(g["clave"])
    lineas = [f"- Semestre {s}: {', '.join(claves)}" for s, claves in por_semestre.items()]
    return (f"Grupos ofertados en {etiqueta_periodo(periodo)}:\n" + "\n".join(lineas) +
            "\n\nV = vespertino, M y S = matutino. Dime un semestre o un grupo para ver más detalles."), \
           [f"Materias del grupo {list(por_semestre.values())[0][0]}"]


def buscar_grupo(bd, periodo, clave):
    return bd.execute(
        """SELECT g.id, g.clave, g.turno, s.numero AS semestre FROM grupos g
           JOIN semestres s ON s.id = g.semestre_id
           WHERE g.periodo_id = ? AND g.clave = ? AND g.estado != 'INACTIVO'""",
        (periodo["id"], clave),
    ).fetchone()


def grupo_no_ofertado(periodo, clave):
    return (f"El grupo {clave} no se oferta en el periodo {etiqueta_periodo(periodo)}. "
            f"Se ofertan los semestres {texto_lista(semestres_ofertados(periodo['tipo']))}.")


def r_materias(bd, periodo, ent):
    ofertados = semestres_ofertados(periodo["tipo"])
    if ent["grupo"]:
        grupo = buscar_grupo(bd, periodo, ent["grupo"])
        if not grupo:
            return grupo_no_ofertado(periodo, ent["grupo"]), MENU
        filas = bd.execute(
            """SELECT m.nombre AS materia, p.nombre AS profesor FROM asignaciones a
               JOIN materias m ON m.id = a.materia_id JOIN profesores p ON p.id = a.profesor_id
               WHERE a.grupo_id = ? ORDER BY m.nombre""", (grupo["id"],)).fetchall()
        lineas = [f"- {f['materia']} — {f['profesor']}" for f in filas]
        return (f"Materias del grupo {grupo['clave']} ({nombre_turno(grupo['turno'])}, "
                f"semestre {grupo['semestre']}):\n" + "\n".join(lineas)), \
               [f"Horario del grupo {grupo['clave']}"]
    if ent["semestre"]:
        if ent["semestre"] not in ofertados:
            return sin_semestre_ofertado(periodo, ent["semestre"]), MENU
        filas = bd.execute(
            """SELECT m.nombre FROM materias m JOIN semestres s ON s.id = m.semestre_id
               WHERE s.numero = ? ORDER BY m.nombre""", (ent["semestre"],)).fetchall()
        return (f"Materias del semestre {ent['semestre']}:\n" + "\n".join(f"- {f['nombre']}" for f in filas)), \
               [f"Grupos del semestre {ent['semestre']}"]
    return "¿De qué semestre o grupo quieres ver las materias? Por ejemplo: «materias del semestre 3» o «materias del grupo V3».", \
           ["Grupos disponibles"]


def asignaciones_de_materias(bd, periodo, ids_materia):
    marcas = ",".join("?" * len(ids_materia))
    return bd.execute(
        f"""SELECT m.id AS materia_id, m.nombre AS materia, g.id AS grupo_id, g.clave, g.turno,
                   p.nombre AS profesor, a.id AS asignacion_id
            FROM asignaciones a
            JOIN materias m ON m.id = a.materia_id JOIN grupos g ON g.id = a.grupo_id
            JOIN profesores p ON p.id = a.profesor_id
            WHERE g.periodo_id = ? AND m.id IN ({marcas})
            ORDER BY m.nombre, g.clave""", (periodo["id"], *ids_materia)).fetchall()


def pedir_aclaracion_materia(ent):
    if len(ent["materias"]) > 1:
        opciones = ent["materias"]
    else:
        opciones = ent["parciales"]
    if not opciones:
        return None
    lineas = "\n".join(f"- {m['nombre']}" for m in opciones)
    texto = ("Encontré varias materias que podrían ser. ¿A cuál te refieres?\n" + lineas) \
        if len(ent["materias"]) > 1 else \
        ("No estoy seguro de qué materia es. ¿Te refieres a alguna de estas?\n" + lineas)
    return texto, [m["nombre"] for m in opciones][:4]


def r_profesores(bd, periodo, ent, contexto):
    if ent["materias"] and len(ent["materias"]) == 1:
        materia = ent["materias"][0]
        filas = asignaciones_de_materias(bd, periodo, [materia["id"]])
        if not filas:
            return (f"La materia {materia['nombre']} no se oferta en el periodo "
                    f"{etiqueta_periodo(periodo)}. Se ofertan los semestres "
                    f"{texto_lista(semestres_ofertados(periodo['tipo']))}."), MENU
        filtro = ent["grupo"] or contexto.get("grupo")
        if filtro and any(f["clave"] == filtro for f in filas):
            filas = [f for f in filas if f["clave"] == filtro]
        por_profesor = {}
        for f in filas:
            por_profesor.setdefault(f["profesor"], []).append(f["clave"])
        lineas = [f"- {prof} (grupos {', '.join(claves)})" for prof, claves in por_profesor.items()]
        return (f"{materia['nombre']} la imparte:\n" + "\n".join(lineas)), \
               [f"Horario de {materia['nombre']}"]
    aclaracion = pedir_aclaracion_materia(ent)
    if aclaracion and (ent["materias"] or not ent["grupo"]):
        return aclaracion
    if ent["profesores"]:
        if len(ent["profesores"]) > 1:
            lineas = "\n".join(f"- {p['nombre']}" for p in ent["profesores"])
            return "Hay varios profesores que coinciden. ¿A cuál te refieres?\n" + lineas, \
                   [p["nombre"] for p in ent["profesores"]][:4]
        prof = ent["profesores"][0]
        filas = bd.execute(
            """SELECT m.nombre AS materia, s.numero AS semestre, g.clave
               FROM asignaciones a JOIN materias m ON m.id = a.materia_id
               JOIN semestres s ON s.id = m.semestre_id JOIN grupos g ON g.id = a.grupo_id
               WHERE a.profesor_id = ? AND g.periodo_id = ?
               ORDER BY s.numero, m.nombre, g.clave""", (prof["id"], periodo["id"])).fetchall()
        if not filas:
            return f"{prof['nombre']} no imparte materias en el periodo {etiqueta_periodo(periodo)}.", MENU
        por_materia = {}
        for f in filas:
            por_materia.setdefault((f["semestre"], f["materia"]), []).append(f["clave"])
        lineas = [f"- {m} (semestre {s}, grupos {', '.join(c)})" for (s, m), c in por_materia.items()]
        return (f"{prof['nombre']} imparte en {etiqueta_periodo(periodo)}:\n" + "\n".join(lineas)), MENU
    grupo = ent["grupo"] or contexto.get("grupo")
    if grupo:
        return r_materias(bd, periodo, {**ent, "grupo": grupo, "semestre": None})
    return "¿De qué materia o grupo quieres saber el profesor? Por ejemplo: «¿Quién imparte Cálculo III?».", MENU


def formato_bloque(f):
    return f"{f['hora_inicio']}-{f['hora_fin']}"


def r_horarios(bd, periodo, ent, contexto):
    if len(ent["materias"]) == 1 or (not ent["grupo"] and (ent["materias"] or ent["parciales"])):
        if len(ent["materias"]) != 1:
            return pedir_aclaracion_materia(ent)
        materia = ent["materias"][0]
        asigs = asignaciones_de_materias(bd, periodo, [materia["id"]])
        if not asigs:
            return (f"La materia {materia['nombre']} no se oferta en el periodo "
                    f"{etiqueta_periodo(periodo)}."), MENU
        filtro = ent["grupo"] or contexto.get("grupo")
        if filtro and any(a["clave"] == filtro for a in asigs):
            asigs = [a for a in asigs if a["clave"] == filtro]
        bloques = []
        for a in asigs:
            horas = bd.execute(
                f"""SELECT h.dia_semana, h.hora_inicio, h.hora_fin, h.salon FROM horarios h
                    WHERE h.asignacion_id = ? ORDER BY {ORDEN_DIAS}, h.hora_inicio""",
                (a["asignacion_id"],)).fetchall()
            detalle = "\n".join(f"  {DIAS[h['dia_semana']]} {formato_bloque(h)} · salón {h['salon']}" for h in horas)
            bloques.append(f"Grupo {a['clave']} ({nombre_turno(a['turno'])}) — {a['profesor']}:\n{detalle}")
        return f"Horarios de {materia['nombre']}:\n\n" + "\n\n".join(bloques), \
               [f"Horario del grupo {asigs[0]['clave']}"]
    grupo_clave = ent["grupo"] or contexto.get("grupo")
    if grupo_clave:
        grupo = buscar_grupo(bd, periodo, grupo_clave)
        if not grupo:
            return grupo_no_ofertado(periodo, grupo_clave), MENU
        filas = bd.execute(
            f"""SELECT h.dia_semana, h.hora_inicio, h.hora_fin, h.salon, m.nombre AS materia
                FROM horarios h JOIN asignaciones a ON a.id = h.asignacion_id
                JOIN materias m ON m.id = a.materia_id
                WHERE a.grupo_id = ? ORDER BY {ORDEN_DIAS}, h.hora_inicio""",
            (grupo["id"],)).fetchall()
        if not filas:
            return f"Todavía no hay horario registrado para el grupo {grupo['clave']}.", MENU
        salones = {f["salon"] for f in filas}
        encabezado = f"Horario del grupo {grupo['clave']} ({nombre_turno(grupo['turno'])})"
        if len(salones) == 1:
            encabezado += f" — salón {next(iter(salones))}"
        por_dia = {}
        for f in filas:
            extra = "" if len(salones) == 1 else f" · salón {f['salon']}"
            por_dia.setdefault(f["dia_semana"], []).append(
                f"  {formato_bloque(f)} · {f['materia']}{extra}")
        cuerpo = "\n\n".join(f"{DIAS[d]}\n" + "\n".join(l) for d, l in por_dia.items())
        return f"{encabezado}:\n\n{cuerpo}", [f"Materias del grupo {grupo['clave']}"]
    if ent["semestre"]:
        if ent["semestre"] not in semestres_ofertados(periodo["tipo"]):
            return sin_semestre_ofertado(periodo, ent["semestre"]), MENU
        claves = [g["clave"] for g in grupos_del_periodo(bd, periodo) if g["semestre"] == ent["semestre"]]
        return (f"¿De qué grupo quieres el horario? En el semestre {ent['semestre']} hay: "
                f"{texto_lista(claves)}."), [f"Horario del grupo {c}" for c in claves]
    return ("¿De qué grupo o materia quieres el horario? Por ejemplo: «horario del grupo V3» o "
            "«¿a qué hora es Ingeniería de Software?»."), ["Grupos disponibles"]


def estrellas(promedio):
    return f"{promedio:.1f}/5"


def r_opiniones(bd, ent, tokens):
    """Opiniones PUBLICADAS de alumnos sobre una materia o un profesor."""
    quiere_ranking = any(t in tokens for t in ("mejor", "mejores", "recomiendan", "recomendado", "recomendable"))
    if ent["materias"] or ent["parciales"]:
        ids = [m["id"] for m in (ent["materias"] or ent["parciales"])]
        marcas = ",".join("?" * len(ids))
        filas = bd.execute(
            f"""SELECT m.nombre AS materia, p.nombre AS profesor, ROUND(AVG(o.calificacion), 1) AS promedio,
                       COUNT(*) AS total
                FROM opiniones o JOIN materias m ON m.id = o.materia_id
                JOIN profesores p ON p.id = o.profesor_id
                WHERE o.estado = 'PUBLICADA' AND o.materia_id IN ({marcas})
                GROUP BY o.materia_id, o.profesor_id ORDER BY promedio DESC, total DESC""", ids).fetchall()
        if not filas:
            return "Todavía no hay opiniones publicadas sobre esa materia.", MENU
        if quiere_ranking or len(ids) > 1:
            lineas = [f"- {f['profesor']} en {f['materia']}: {estrellas(f['promedio'])} ({f['total']} opiniones)"
                      for f in filas[:5]]
            return "Calificación promedio de los alumnos:\n" + "\n".join(lineas), MENU
        f = filas[0]
        comentarios = bd.execute(
            """SELECT calificacion, comentario FROM opiniones
               WHERE estado = 'PUBLICADA' AND materia_id = ? ORDER BY fecha_registro DESC, id DESC LIMIT 3""",
            (ids[0],)).fetchall()
        detalle = "\n".join(f"  · {c['calificacion']}/5 — «{c['comentario']}»" for c in comentarios)
        return (f"{f['materia']} con {f['profesor']}: {estrellas(f['promedio'])} "
                f"({f['total']} opiniones). Algunos comentarios:\n{detalle}"), \
               [f"Horario de {f['materia']}"]
    if ent["profesores"] and len(ent["profesores"]) == 1:
        prof = ent["profesores"][0]
        resumen = bd.execute(
            """SELECT ROUND(AVG(calificacion), 1) AS promedio, COUNT(*) AS total FROM opiniones
               WHERE estado = 'PUBLICADA' AND profesor_id = ?""", (prof["id"],)).fetchone()
        if not resumen["total"]:
            return f"Todavía no hay opiniones publicadas sobre {prof['nombre']}.", MENU
        comentarios = bd.execute(
            """SELECT m.nombre AS materia, o.calificacion, o.comentario FROM opiniones o
               JOIN materias m ON m.id = o.materia_id
               WHERE o.estado = 'PUBLICADA' AND o.profesor_id = ?
               ORDER BY o.fecha_registro DESC, o.id DESC LIMIT 3""", (prof["id"],)).fetchall()
        detalle = "\n".join(f"  · {c['materia']}, {c['calificacion']}/5 — «{c['comentario']}»" for c in comentarios)
        return (f"{prof['nombre']}: {estrellas(resumen['promedio'])} ({resumen['total']} opiniones). "
                f"Algunos comentarios:\n{detalle}"), MENU
    return ("¿Sobre qué materia o profesor quieres ver opiniones? Por ejemplo: "
            "«opiniones de Cálculo III» o «¿qué profesor tiene mejores opiniones en programación?». "
            "Si quieres dejar tu propia opinión, usa el formulario de opiniones."), MENU

# ---------- punto de entrada ----------
def responder(bd: sqlite3.Connection, texto, contexto):
    materias = bd.execute("SELECT id, nombre FROM materias").fetchall()
    profesores = bd.execute("SELECT id, nombre FROM profesores").fetchall()
    analisis = pln.procesar(texto, construir_vocabulario(materias, profesores))
    normalizado, corregidos = analisis["normalizado"], analisis["corregidos"]

    candidatas, parciales = buscar_materias(materias, analisis["raices"], analisis["tokens"])
    ent = {
        "semestre": extraer_semestre(normalizado, analisis["tokens"]),
        "grupo": extraer_grupo(normalizado),
        "turnos": extraer_turnos(normalizado),
        "materias": candidatas,
        "parciales": parciales,
        "profesores": buscar_profesores(profesores, corregidos),
    }
    if ent["grupo"] and not ent["semestre"]:
        ent["semestre"] = int(ent["grupo"][1:])

    intencion = detectar_intencion(analisis["raices"], ent)
    periodo = cargar_periodo(bd)
    necesita_periodo = intencion in {"PERIODO", "GRUPOS", "MATERIAS", "PROFESORES", "HORARIOS"}
    if necesita_periodo and not periodo:
        respuesta, sugerencias = ("Todavía no hay un periodo escolar activo. "
                                  "El administrador debe configurarlo desde el dashboard."), []
    elif intencion == "SALUDO":
        respuesta, sugerencias = r_saludo()
    elif intencion == "DESPEDIDA":
        respuesta, sugerencias = r_despedida()
    elif intencion == "AYUDA":
        respuesta, sugerencias = r_ayuda()
    elif intencion == "PERIODO":
        respuesta, sugerencias = r_periodo(bd, periodo)
    elif intencion == "GRUPOS":
        respuesta, sugerencias = r_grupos(bd, periodo, ent)
    elif intencion == "MATERIAS":
        if not (ent["grupo"] or ent["semestre"]) and contexto.get("grupo"):
            ent["grupo"] = contexto["grupo"]
        respuesta, sugerencias = r_materias(bd, periodo, ent)
    elif intencion == "PROFESORES":
        respuesta, sugerencias = r_profesores(bd, periodo, ent, contexto)
    elif intencion == "HORARIOS":
        respuesta, sugerencias = r_horarios(bd, periodo, ent, contexto)
    elif intencion == "OPINIONES":
                respuesta, sugerencias = r_opiniones(bd, ent, analisis["tokens"])
    else:
        respuesta = ("No estoy seguro de haber entendido. Puedo ayudarte con grupos, materias, "
                     "profesores y horarios. Escribe «ayuda» para ver ejemplos.")
        sugerencias = MENU

    if ent["grupo"]:
        contexto["grupo"] = ent["grupo"]
    return {"respuesta": respuesta, "intencion": intencion, "sugerencias": sugerencias}