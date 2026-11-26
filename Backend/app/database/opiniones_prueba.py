import random
import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"

# Datos de PRUEBA. Se reemplazan por opiniones reales cuando haya alumnos que opinen.
COMENTARIOS = {
    5: ["Explica muy claro y siempre resuelve dudas.", "Excelente clase, se aprende mucho.",
        "Muy buen manejo del tema y ejemplos prácticos."],
    4: ["Buena clase, solo deja bastante tarea.", "Explica bien, los exámenes son justos.",
        "Recomendable, aunque el ritmo es rápido."],
    3: ["Clase regular, depende mucho del estudio personal.", "Cumple con el temario, sin más.",
        "A veces cuesta seguir el ritmo."],
    2: ["Los exámenes son más difíciles que lo visto en clase.", "Le falta claridad al explicar."],
}
PESOS = [5, 5, 5, 4, 4, 4, 3, 3, 2]


def cargar():
    random.seed(2026)
    con = sqlite3.connect(RUTA_BD)
    con.execute("PRAGMA foreign_keys = ON")
    if con.execute("SELECT COUNT(*) FROM opiniones").fetchone()[0] > 0:
        print("Ya hay opiniones cargadas. Para repetir la carga, recrea la base de datos.")
        con.close()
        return
    periodo = con.execute("SELECT id FROM periodos_escolares WHERE activo = 1").fetchone()
    pares = con.execute(
        "SELECT DISTINCT materia_id, profesor_id FROM asignaciones ORDER BY materia_id"
    ).fetchall()
    total = 0
    for materia_id, profesor_id in pares:
        for n in range(random.randint(2, 4)):
            nota = random.choice(PESOS)
            con.execute(
                """INSERT INTO opiniones
                   (materia_id, profesor_id, periodo_id, autor_alias, calificacion, comentario, estado)
                   VALUES (?, ?, ?, ?, ?, ?, 'PUBLICADA')""",
                (materia_id, profesor_id, periodo[0] if periodo else None,
                 f"Alumno de prueba {n + 1}", nota, random.choice(COMENTARIOS[nota])),
            )
            total += 1
    con.commit()
    print(f"Opiniones de prueba cargadas: {total}")
    con.close()


if __name__ == "__main__":
    cargar()