import { useState } from 'react'
import { pedir } from '../api'
import { useDatos } from '../useDatos'

const PESTANAS = [
  ['pendientes', 'Pendientes'],
  ['publicadas', 'Publicadas'],
  ['resumen', 'Resumen por profesor'],
]

function Estrellas({ valor }) {
  return (
    <span className="estrellas" role="img" aria-label={`${valor} de 5`}>
      {'★'.repeat(valor)}
      {'☆'.repeat(5 - valor)}
    </span>
  )
}

function ListaOpiniones({ ruta, acciones, textoVacio }) {
  const { datos, error, cargando, recargar } = useDatos(ruta)
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)

  async function moderar(id, estado, textoExito) {
    setOcupado(true)
    setMensaje(null)
    try {
      await pedir(`/opiniones/${id}/estado`, { metodo: 'PUT', cuerpo: { estado } })
      setMensaje({ texto: textoExito, error: false })
      await recargar()
    } catch (e) {
      setMensaje({ texto: e.message, error: true })
    } finally {
      setOcupado(false)
    }
  }

  return (
    <>
      {mensaje && (
        <p className={'aviso' + (mensaje.error ? ' aviso--error' : ' aviso--exito')} role="status">
          {mensaje.texto}
        </p>
      )}
      {cargando && <p className="vacio">Cargando…</p>}
      {error && (
        <p className="aviso aviso--error" role="alert">
          {error}
        </p>
      )}
      {datos?.length === 0 && <p className="vacio">{textoVacio}</p>}
      <ul className="opiniones">
        {(datos ?? []).map((opinion) => (
          <li key={opinion.id} className="tarjeta opinion-tarjeta">
            <div className="opinion-tarjeta__cabecera">
              <strong>{opinion.materia}</strong>
              <span>{opinion.profesor}</span>
              <Estrellas valor={opinion.calificacion} />
            </div>
            <p className="opinion-tarjeta__comentario">«{opinion.comentario}»</p>
            <div className="opinion-tarjeta__pie">
              <span className="vacio">
                {opinion.autor_alias ?? 'Anónimo'} · {opinion.fecha_registro?.slice(0, 10)}
              </span>
              <span className="acciones">
                {acciones.map(([estado, texto, textoExito, secundario]) => (
                  <button
                    key={estado}
                    type="button"
                    className={secundario ? 'boton-secundario' : undefined}
                    disabled={ocupado}
                    onClick={() => moderar(opinion.id, estado, textoExito)}
                  >
                    {texto}
                  </button>
                ))}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </>
  )
}

function Resumen() {
  const { datos, error, cargando } = useDatos('/opiniones/resumen')
  return (
    <section className="tarjeta">
      {cargando && <p className="vacio">Cargando…</p>}
      {error && (
        <p className="aviso aviso--error" role="alert">
          {error}
        </p>
      )}
      {datos?.length === 0 && <p className="vacio">Todavía no hay opiniones publicadas.</p>}
      {datos?.length > 0 && (
        <div className="tabla-contenedor">
          <table className="tabla">
            <thead>
              <tr>
                <th>Materia</th>
                <th>Profesor</th>
                <th>Promedio</th>
                <th>Opiniones</th>
              </tr>
            </thead>
            <tbody>
              {datos.map((fila) => (
                <tr key={`${fila.materia}-${fila.profesor}`}>
                  <td>{fila.materia}</td>
                  <td>{fila.profesor}</td>
                  <td>{fila.promedio.toFixed(1)} / 5</td>
                  <td>{fila.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default function Opiniones() {
  const [pestana, setPestana] = useState('pendientes')

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Opiniones</h1>
        <p>
          Las opiniones que envían los alumnos llegan como pendientes. Solo las que publiques aparecen en el chatbot y
          cuentan para el promedio de cada profesor.
        </p>
      </header>

      <div className="pestanas" role="tablist" aria-label="Opiniones">
        {PESTANAS.map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={pestana === clave}
            className={pestana === clave ? 'pestana pestana--activa' : 'pestana'}
            onClick={() => setPestana(clave)}
          >
            {texto}
          </button>
        ))}
      </div>

      {pestana === 'pendientes' && (
        <ListaOpiniones
          key="pendientes"
          ruta="/opiniones/pendientes"
          textoVacio="No hay opiniones por revisar. 🎉"
          acciones={[
            ['PUBLICADA', 'Publicar', 'Opinión publicada.'],
            ['RECHAZADA', 'Rechazar', 'Opinión rechazada.', true],
          ]}
        />
      )}
      {pestana === 'publicadas' && (
        <ListaOpiniones
          key="publicadas"
          ruta="/opiniones"
          textoVacio="Todavía no hay opiniones publicadas."
          acciones={[['RECHAZADA', 'Retirar', 'Opinión retirada.', true]]}
        />
      )}
      {pestana === 'resumen' && <Resumen />}
    </>
  )
}