import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"


def obtener_conexion():
    conexion = sqlite3.connect(RUTA_BD, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def obtener_bd():
    conexion = obtener_conexion()
    try:
        yield conexion
    finally:
        conexion.close()