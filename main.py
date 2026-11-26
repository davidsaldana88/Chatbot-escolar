import sqlite3
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.database.conexion import obtener_bd
from app.reglas import semestres_ofertados

from app.consultas import router as router_consultas

from app.chatbot.rutas import router as router_chatbot
from app.opiniones import router as router_opiniones
from app.administracion import router as router_administracion
from app.seguridad import router as router_seguridad, requerir_admin

app = FastAPI(title="Chatbot Escolar - Ingeniería en Sistemas Inteligentes")
app.include_router(router_consultas)
app.include_router(router_chatbot)
app.include_router(router_opiniones)
app.include_router(router_administracion, dependencies=[Depends(requerir_admin)])
app.include_router(router_seguridad)

class PeriodoEntrada(BaseModel):
    anio: int
    tipo: Literal["ENERO_JUNIO", "AGOSTO_DICIEMBRE"]


def obtener_periodo_activo(bd: sqlite3.Connection):
    return bd.execute(
        "SELECT * FROM periodos_escolares WHERE activo = 1"
    ).fetchone()


@app.get("/")
def raiz():
    return {"mensaje": "API del chatbot escolar funcionando"}


@app.get("/semestres")
def listar_semestres(bd: sqlite3.Connection = Depends(obtener_bd)):
    filas = bd.execute(
        "SELECT id, numero, nombre FROM semestres ORDER BY numero"
    ).fetchall()
    return [dict(fila) for fila in filas]


@app.put("/periodos/activar")
def activar_periodo(datos: PeriodoEntrada, bd: sqlite3.Connection = Depends(obtener_bd)):
    # Solo puede haber un periodo activo: primero apagamos todos.
    bd.execute("UPDATE periodos_escolares SET activo = 0")
    existente = bd.execute(
        "SELECT id FROM periodos_escolares WHERE anio = ? AND tipo = ?",
        (datos.anio, datos.tipo),
    ).fetchone()
    if existente:
        bd.execute(
            "UPDATE periodos_escolares SET activo = 1 WHERE id = ?",
            (existente["id"],),
        )
    else:
        bd.execute(
            "INSERT INTO periodos_escolares (anio, tipo, activo) VALUES (?, ?, 1)",
            (datos.anio, datos.tipo),
        )
    bd.commit()
    periodo = obtener_periodo_activo(bd)
    return {**dict(periodo), "semestres_ofertados": semestres_ofertados(periodo["tipo"])}


@app.get("/periodo-activo")
def periodo_activo(bd: sqlite3.Connection = Depends(obtener_bd)):
    periodo = obtener_periodo_activo(bd)
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay un periodo escolar activo")
    return {**dict(periodo), "semestres_ofertados": semestres_ofertados(periodo["tipo"])}


@app.get("/semestres/ofertados")
def semestres_del_periodo(bd: sqlite3.Connection = Depends(obtener_bd)):
    periodo = obtener_periodo_activo(bd)
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay un periodo escolar activo")
    numeros = semestres_ofertados(periodo["tipo"])
    marcas = ",".join("?" * len(numeros))
    filas = bd.execute(
        f"SELECT id, numero, nombre FROM semestres WHERE numero IN ({marcas}) ORDER BY numero",
        numeros,
    ).fetchall()
    return [dict(fila) for fila in filas]