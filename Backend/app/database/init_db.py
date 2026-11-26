
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "chatbot_escolar.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def inicializar_base_datos():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conexion:
        conexion.execute("PRAGMA foreign_keys = ON;")

        # Crear las tablas
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conexion.executescript(schema)

        # Registrar el programa académico
        conexion.execute("""
            INSERT OR IGNORE INTO programas (nombre, descripcion)
            VALUES (?, ?)
        """, (
            "Ingeniería en Sistemas Inteligentes",
            "Programa académico organizado en 10 semestres."
        ))

        # Registrar los 10 semestres
        for numero in range(1, 11):
            conexion.execute("""
                INSERT OR IGNORE INTO semestres (numero, nombre)
                VALUES (?, ?)
            """, (
                numero,
                f"{numero}° semestre"
            ))

        conexion.commit()

    print("Base de datos inicializada correctamente.")
    print("Programa académico registrado.")
    print("10 semestres registrados.")
    print(f"Ubicación: {DB_PATH}")


if __name__ == "__main__":
    inicializar_base_datos()
