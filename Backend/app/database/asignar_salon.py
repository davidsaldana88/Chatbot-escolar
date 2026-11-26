import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"

SALONES = ["E1", "E2", "E3", "E4", "E5", "L1", "L2", "L3", "L4", "L5"]


def asignar(con):
    """Cada grupo conserva un solo salón toda la semana.

    Los grupos matutinos y vespertinos nunca coinciden en horario (el matutino
    termina a las 14:00 como muy tarde y el vespertino empieza a las 14:00),
    así que cada turno puede usar los 10 salones.
    """
    grupos = con.execute(
        """SELECT g.id, g.turno, g.periodo_id
           FROM grupos g JOIN semestres s ON s.id = g.semestre_id
           ORDER BY g.periodo_id, g.turno, s.numero, g.clave"""
    ).fetchall()
    contador = {}
    salon_de_grupo = {}
    for grupo_id, turno, periodo_id in grupos:
        clave = (periodo_id, turno)
        i = contador.get(clave, 0)
        salon_de_grupo[grupo_id] = SALONES[i % len(SALONES)]
        contador[clave] = i + 1
        if i >= len(SALONES):
            print(f"  Aviso: hay más grupos {turno} que salones; se comparten salones.")

    con.executemany(
        """UPDATE horarios SET salon = ?
           WHERE asignacion_id IN (SELECT id FROM asignaciones WHERE grupo_id = ?)""",
        [(salon, grupo_id) for grupo_id, salon in salon_de_grupo.items()],
    )
    con.commit()
    return len(salon_de_grupo)


def verificar(con):
    n = con.execute(
        """SELECT COUNT(*) FROM horarios h1 JOIN horarios h2
             ON h1.salon = h2.salon AND h1.dia_semana = h2.dia_semana
            AND h1.hora_inicio < h2.hora_fin AND h2.hora_inicio < h1.hora_fin AND h1.id < h2.id
           JOIN asignaciones a1 ON a1.id = h1.asignacion_id
           JOIN asignaciones a2 ON a2.id = h2.asignacion_id
           JOIN grupos g1 ON g1.id = a1.grupo_id
           JOIN grupos g2 ON g2.id = a2.grupo_id
           WHERE g1.periodo_id = g2.periodo_id"""
    ).fetchone()[0]
    print(f"  choques de salón: {n}")
    return n == 0


if __name__ == "__main__":
    con = sqlite3.connect(RUTA_BD)
    columnas = [fila[1] for fila in con.execute("PRAGMA table_info(horarios)")]
    if "salon" not in columnas:
        print("La base no tiene la columna 'salon'. Revisa schema.sql y recrea la base.")
    elif con.execute("SELECT COUNT(*) FROM horarios").fetchone()[0] == 0:
        print("Primero ejecuta generar_horarios.py")
    else:
        total = asignar(con)
        print(f"Salón asignado a {total} grupos")
        print("Verificación:")
        print("Todo correcto." if verificar(con) else "HAY CHOQUES, avísame.")
        print("Salón de cada grupo (ejemplo):")
        for fila in con.execute(
            """SELECT g.clave, g.turno, h.salon FROM horarios h
               JOIN asignaciones a ON a.id = h.asignacion_id
               JOIN grupos g ON g.id = a.grupo_id
               GROUP BY g.id ORDER BY g.periodo_id, g.turno, g.clave LIMIT 6"""
        ):
            print(f"  {fila[0]} ({fila[1]}): {fila[2]}")
    con.close()