import random
import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"

ANIO = 2026
TURNOS = {"V": "VESPERTINO", "M": "MATUTINO", "S": "SABATINO"}
CUPO_PRUEBA = 30  # dato de prueba

RETICULA = {
    1: ["Psicología", "Álgebra Superior", "Cálculo I", "Matemáticas Discretas",
        "Geometría Analítica", "Fundamentos de Programación"],
    2: ["Inglés C1", "Álgebra Lineal", "Cálculo II", "Ecuaciones Diferenciales",
        "Lenguajes y Autómatas", "Programación Orientada a Objetos"],
    3: ["Inglés C2", "Cálculo III", "Probabilidad y Estadística", "Física Básica",
        "Estructura de Datos", "Lógica Matemática"],
    4: ["Electricidad y Magnetismo", "Química", "Metrología", "Organización de Archivos",
        "Introducción a la Inteligencia Artificial", "Psicología Avanzada"],
    5: ["Circuitos Eléctricos", "Métodos Numéricos", "Lenguaje Ensamblador",
        "Programación Web", "Fundamentos de Bases de Datos",
        "Introducción al Tratamiento de Imágenes"],
    6: ["Arquitectura de Computadoras", "Compiladores", "Sistemas Basados en Conocimiento",
        "Bases de Datos Distribuidas", "Introducción al Reconocimiento de Patrones",
        "Preparación de Datos"],
    7: ["Redes de Computadoras I", "Sistemas Operativos", "Ingeniería de Software",
        "Árboles de Decisión", "Minería de Datos I", "Data Warehouse I",
        "Evaluación e Interpretación del Conocimiento"],
    8: ["Redes de Computadoras II", "Sistemas Operativos Distribuidos", "Minería de Datos II",
        "Visualización de Datos", "Redes Neuronales Supervisadas", "Data Warehouse II",
        "Interpretación de Imágenes"],
    9: ["Algoritmos de Clasificación", "Algoritmos de Agrupamiento",
        "Procesamiento de Lenguaje Natural",
        "Reconocimiento de Patrones Sintáctico-Estructural",
        "Redes Neuronales No Supervisadas", "Algoritmos Genéticos"],
    10: ["Taller de Tesis", "Robótica", "Lógica Difusa", "Práctica Profesional",
         "Taller con Weka", "Taller de Minería de Datos", "Redes Neuronales Modulares",
         "Razonamiento Basado en Casos", "Graficación", "Programación con MATLAB"],
}

PROFESORES = {
    "Dr. en I. en Sis. Ricardo Rico Molina": [
        "Matemáticas Discretas", "Métodos Numéricos", "Arquitectura de Computadoras",
        "Minería de Datos II", "Interpretación de Imágenes",
        "Probabilidad y Estadística", "Taller de Minería de Datos"],
    "Dr. en F.M. Israel Gutiérrez González": [
        "Álgebra Superior", "Cálculo III", "Electricidad y Magnetismo",
        "Algoritmos de Clasificación", "Ecuaciones Diferenciales", "Metrología"],
    "M. en C. José Antonio Castillo Jiménez": [
        "Cálculo I", "Cálculo II", "Circuitos Eléctricos", "Redes Neuronales Supervisadas",
        "Redes Neuronales No Supervisadas", "Redes Neuronales Modulares"],
    "M. en I.S. Yaroslaf Aarón Albarrán Fernández": [
        "Estructura de Datos", "Lenguaje Ensamblador", "Compiladores", "Sistemas Operativos",
        "Robótica"],
    "I. en C. Saúl Steve Torres Ledesma": [
        "Lógica Matemática", "Programación Web", "Redes de Computadoras II",
        "Redes de Computadoras I"],
    "Dr. en I. en Sis. Carmen Liliana Rodríguez Páez": [
        "Sistemas Basados en Conocimiento", "Árboles de Decisión", "Data Warehouse I",
        "Introducción a la Inteligencia Artificial", "Minería de Datos I", "Lógica Difusa"],
    "I. en S. I. Brayan Jorge Nava Beltrán": [
        "Data Warehouse II", "Introducción al Reconocimiento de Patrones",
        "Algoritmos Genéticos", "Procesamiento de Lenguaje Natural",
        "Reconocimiento de Patrones Sintáctico-Estructural"],
    "Dr. en Inv. Edu. Roberto Navarrete Barrera": [
        "Inglés C1", "Inglés C2", "Psicología", "Psicología Avanzada"],
    "Ing. Mec. Octavio Juárez Barrera": [
        "Álgebra Lineal", "Física Básica", "Geometría Analítica", "Química",
        "Programación con MATLAB"],
    "D. en C. TIC María del Carmen Cedillo Chagoya": [
        "Lenguajes y Autómatas", "Organización de Archivos", "Taller de Tesis"],
    "Lic. en I. Amador Ibarra Luna": [
        "Fundamentos de Bases de Datos", "Visualización de Datos", "Preparación de Datos"],
    "I. en S. I. Ricardo Román Cuevas": [
        "Bases de Datos Distribuidas", "Introducción al Tratamiento de Imágenes",
        "Taller con Weka"],
    "I. en C. Rodolfo Vázquez Morales": [
        "Ingeniería de Software", "Sistemas Operativos Distribuidos", "Práctica Profesional"],
    "José Sergio Sosa Vázquez": [
        "Evaluación e Interpretación del Conocimiento", "Algoritmos de Agrupamiento",
        "Razonamiento Basado en Casos"],
    "M. en C. Com. Efrén González Gómez": [
        "Programación Orientada a Objetos", "Fundamentos de Programación", "Graficación"],
}


def cargar():
    random.seed(2026)  # mismo resultado cada vez que se ejecute

    # Validación: toda materia de los profesores debe existir en la retícula
    todas = {m for lista in RETICULA.values() for m in lista}
    for profesor, materias in PROFESORES.items():
        for materia in materias:
            if materia not in todas:
                raise ValueError(f"'{materia}' ({profesor}) no está en la retícula")

    docentes_por_materia = {}
    for profesor, materias in PROFESORES.items():
        for materia in materias:
            docentes_por_materia.setdefault(materia, []).append(profesor)

    con = sqlite3.connect(RUTA_BD)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    if cur.execute("SELECT COUNT(*) FROM materias").fetchone()[0] > 0:
        print("Los datos ya estaban cargados. Para volver a cargarlos, borra")
        print("backend/data/chatbot_escolar.db, ejecuta init_db.py y luego este script.")
        con.close()
        return

    programa_id = cur.execute("SELECT id FROM programas").fetchone()[0]
    semestre_id = {n: i for i, n in cur.execute("SELECT id, numero FROM semestres")}

    # Periodos (el de agosto-diciembre queda activo)
    periodo_id = {}
    for tipo in ("ENERO_JUNIO", "AGOSTO_DICIEMBRE"):
        cur.execute(
            "INSERT OR IGNORE INTO periodos_escolares (anio, tipo, activo) VALUES (?, ?, 0)",
            (ANIO, tipo),
        )
        periodo_id[tipo] = cur.execute(
            "SELECT id FROM periodos_escolares WHERE anio = ? AND tipo = ?", (ANIO, tipo)
        ).fetchone()[0]
    cur.execute("UPDATE periodos_escolares SET activo = 0")
    cur.execute(
        "UPDATE periodos_escolares SET activo = 1 WHERE id = ?",
        (periodo_id["AGOSTO_DICIEMBRE"],),
    )

    # Profesores
    profesor_id = {}
    for nombre in PROFESORES:
        cur.execute("INSERT INTO profesores (nombre) VALUES (?)", (nombre,))
        profesor_id[nombre] = cur.lastrowid

    # Materias
    materia_id = {}
    for numero, materias in RETICULA.items():
        for nombre in materias:
            cur.execute(
                "INSERT INTO materias (programa_id, semestre_id, nombre) VALUES (?, ?, ?)",
                (programa_id, semestre_id[numero], nombre),
            )
            materia_id[nombre] = cur.lastrowid

    # Grupos y asignaciones
    total_grupos = 0
    total_asignaciones = 0
    for numero, materias in RETICULA.items():
        tipo = "AGOSTO_DICIEMBRE" if numero % 2 == 1 else "ENERO_JUNIO"
        for letra, turno in TURNOS.items():
            cur.execute(
                """INSERT INTO grupos
                   (programa_id, semestre_id, periodo_id, clave, turno, cupo, estado)
                   VALUES (?, ?, ?, ?, ?, ?, 'DISPONIBLE')""",
                (programa_id, semestre_id[numero], periodo_id[tipo],
                 f"{letra}{numero}", turno, CUPO_PRUEBA),
            )
            grupo_id = cur.lastrowid
            total_grupos += 1
            for materia in materias:
                docentes = docentes_por_materia.get(materia)
                if not docentes:
                    continue  # materia sin profesor todavía
                docente = random.choice(docentes)
                cur.execute(
                    "INSERT INTO asignaciones (grupo_id, materia_id, profesor_id) VALUES (?, ?, ?)",
                    (grupo_id, materia_id[materia], profesor_id[docente]),
                )
                total_asignaciones += 1

    con.commit()
    con.close()

    sin_profesor = len(materia_id) - len(docentes_por_materia)
    print("Carga completada.")
    print(f"  Profesores:    {len(profesor_id)}")
    print(f"  Materias:      {len(materia_id)} ({sin_profesor} sin profesor asignado)")
    print(f"  Grupos:        {total_grupos}")
    print(f"  Asignaciones:  {total_asignaciones}")


if __name__ == "__main__":
    cargar()