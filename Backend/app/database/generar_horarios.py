import random
import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"

SALONES = ["E1", "E2", "E3", "E4", "E5", "L1", "L2", "L3", "L4", "L5"]
DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
VENTANAS_MATUTINO = [(7, 12), (7, 13), (9, 13), (8, 12), (7, 14)]
VENTANAS_VESPERTINO = [(14, 17), (14, 18), (14, 19)]
BLOQUES = {1: [1], 2: [2], 3: [2, 1], 4: [2, 2]}
OCUPACIONES = [0.8, 0.65, 0.5]
INTENTOS = 300


def hora(h):
    return f"{h:02d}:00"


def horas_por_materia(n, ventana):
    capacidad = (ventana[1] - ventana[0]) * len(DIAS)
    total = min(int(capacidad * OCUPACION[0]), 4 * n)
    base = total // n
    extra = total - base * n
    return [min(4, base + (1 if i < extra else 0)) for i in range(n)]


OCUPACION = [0.8]


def intentar(grupos, rng):
    ocupado_grupo = {}
    ocupado_prof = {}
    filas = []

    carga_prof = {}
    tareas = []
    for g in grupos:
        horas = horas_por_materia(len(g["asignaciones"]), g["ventana"])
        for asig, h in zip(g["asignaciones"], horas):
            tareas.append((g, asig, h))
            carga_prof[asig["profesor_id"]] = carga_prof.get(asig["profesor_id"], 0) + h

    tareas.sort(key=lambda t: -(carga_prof[t[1]["profesor_id"]] + rng.random() * 6))

    for g, asig, h in tareas:
        dias_usados = set()
        for largo in BLOQUES[h]:
            mejor = None
            for dia in DIAS:
                if dia in dias_usados:
                    continue
                libres_g = ocupado_grupo.setdefault((g["id"], dia), set())
                libres_p = ocupado_prof.setdefault((asig["profesor_id"], dia), set())
                for inicio in range(g["ventana"][0], g["ventana"][1] - largo + 1):
                    rango = range(inicio, inicio + largo)
                    if any(x in libres_g or x in libres_p for x in rango):
                        continue
                    puntaje = len(libres_g) + (inicio - g["ventana"][0]) * 0.3 + rng.random() * 1.2
                    if mejor is None or puntaje < mejor[0]:
                        mejor = (puntaje, dia, inicio)
            if mejor is None:
                return None
            _, dia, inicio = mejor
            for x in range(inicio, inicio + largo):
                ocupado_grupo[(g["id"], dia)].add(x)
                ocupado_prof[(asig["profesor_id"], dia)].add(x)
            dias_usados.add(dia)
            filas.append((asig["id"], dia, hora(inicio), hora(inicio + largo), g["salon"]))
    return filas


def generar(con):
    cur = con.cursor()
    cur.execute("UPDATE grupos SET turno = 'MATUTINO' WHERE clave LIKE 'S%'")
    cur.execute("UPDATE grupos SET turno = 'MATUTINO' WHERE clave LIKE 'M%'")
    cur.execute("UPDATE grupos SET turno = 'VESPERTINO' WHERE clave LIKE 'V%'")

    grupos = cur.execute(
        """SELECT g.id, g.clave, g.turno, g.periodo_id, s.numero
           FROM grupos g JOIN semestres s ON s.id = g.semestre_id
           ORDER BY g.periodo_id, s.numero, g.clave"""
    ).fetchall()
    asignaciones = cur.execute("SELECT id, grupo_id, profesor_id FROM asignaciones ORDER BY id").fetchall()

    por_periodo = {}
    for g in grupos:
        por_periodo.setdefault(g[3], []).append(
            {"id": g[0], "clave": g[1], "turno": g[2], "numero": g[4],
             "asignaciones": [{"id": a[0], "profesor_id": a[2]} for a in asignaciones if a[1] == g[0]]}
        )

    cur.execute("DELETE FROM horarios")
    total = 0
    for periodo, lista in por_periodo.items():
        for turno, ventanas in (("MATUTINO", VENTANAS_MATUTINO), ("VESPERTINO", VENTANAS_VESPERTINO)):
            for i, g in enumerate([x for x in lista if x["turno"] == turno]):
                g["ventana"] = ventanas[i % len(ventanas)]
                g["salon"] = SALONES[i % len(SALONES)]
        resultado = None
        for ocup in OCUPACIONES:
            OCUPACION[0] = ocup
            for intento in range(INTENTOS):
                resultado = intentar(lista, random.Random(2026 + intento))
                if resultado:
                    break
            if resultado:
                break
        if not resultado:
            raise RuntimeError(f"No se encontró horario sin choques para el periodo {periodo}")
        cur.executemany(
            "INSERT INTO horarios (asignacion_id, dia_semana, hora_inicio, hora_fin, salon) VALUES (?,?,?,?,?)",
            resultado,
        )
        total += len(resultado)
        print(f"  Periodo {periodo}: {len(resultado)} bloques (ocupación {ocup}, intento {intento + 1})")
    con.commit()
    return total


def verificar(con):
    traslape = "h1.dia_semana = h2.dia_semana AND h1.hora_inicio < h2.hora_fin AND h2.hora_inicio < h1.hora_fin AND h1.id < h2.id"
    base = """FROM horarios h1 JOIN horarios h2 ON {t}
              JOIN asignaciones a1 ON a1.id = h1.asignacion_id
              JOIN asignaciones a2 ON a2.id = h2.asignacion_id
              JOIN grupos g1 ON g1.id = a1.grupo_id
              JOIN grupos g2 ON g2.id = a2.grupo_id
              WHERE g1.periodo_id = g2.periodo_id AND {c}""".format(t=traslape, c="{c}")
    chequeos = {
        "choques de profesor": "a1.profesor_id = a2.profesor_id",
        "choques de grupo": "a1.grupo_id = a2.grupo_id",
        "choques de salon": "h1.salon = h2.salon",
    }
    ok = True
    for nombre, cond in chequeos.items():
        n = con.execute("SELECT COUNT(*) " + base.format(c=cond)).fetchone()[0]
        print(f"  {nombre}: {n}")
        ok = ok and n == 0
    return ok


if __name__ == "__main__":
    con = sqlite3.connect(RUTA_BD)
    con.execute("PRAGMA foreign_keys = ON")
    if con.execute("SELECT COUNT(*) FROM asignaciones").fetchone()[0] == 0:
        print("Primero ejecuta cargar_datos.py")
    else:
        print("Generando horarios...")
        total = generar(con)
        print(f"Horarios generados: {total} bloques")
        print("Verificación:")
        print("Todo correcto." if verificar(con) else "HAY CHOQUES, avísame.")
    con.close()