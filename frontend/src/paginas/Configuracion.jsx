import { useState } from 'react'
import { pedir } from '../api'
import { useDatos } from '../useDatos'

const NOMBRES_PERIODO = { ENERO_JUNIO: 'Enero–Junio', AGOSTO_DICIEMBRE: 'Agosto–Diciembre' }

export default function Configuracion() {
  const { datos, error, cargando, recargar } = useDatos('/admin/periodos')
  const [anio, setAnio] = useState(new Date().getFullYear())
  const [tipo, setTipo] = useState('AGOSTO_DICIEMBRE')
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  async function activar(anioElegido, tipoElegido) {
    setGuardando(true)
    setMensaje(null)
    try {
      await pedir('/periodos/activar', { metodo: 'PUT', cuerpo: { anio: Number(anioElegido), tipo: tipoElegido } })
      setMensaje({ texto: `Periodo activo: ${NOMBRES_PERIODO[tipoElegido]} ${anioElegido}.`, error: false })
      await recargar()
    } catch (e) {
      setMensaje({ texto: e.message, error: true })
    } finally {
      setGuardando(false)
    }
  }

  function alEnviar(evento) {
    evento.preventDefault()
    activar(anio, tipo)
  }

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Configuración</h1>
        <p>
          El periodo activo decide qué semestres se ofertan: enero–junio ofrece los pares y agosto–diciembre los
          impares. El chatbot usa este periodo en todas sus respuestas.
        </p>
      </header>

      {mensaje && (
        <p className={'aviso' + (mensaje.error ? ' aviso--error' : ' aviso--exito')} role="status">
          {mensaje.texto}
        </p>
      )}

      <section className="tarjeta">
        <h2>Periodos escolares</h2>
        {cargando && <p className="vacio">Cargando…</p>}
        {error && (
          <p className="aviso aviso--error" role="alert">
            {error}
          </p>
        )}
        {datos && (
          <table className="tabla">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Semestres que se ofertan</th>
                <th>Estado</th>
                <th>
                  <span className="solo-lectores">Acción</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {datos.map((periodo) => (
                <tr key={periodo.id}>
                  <td>
                    {NOMBRES_PERIODO[periodo.tipo]} {periodo.anio}
                  </td>
                  <td>{periodo.semestres_ofertados.join(', ')}</td>
                  <td>{periodo.activo ? <span className="etiqueta etiqueta--activa">Activo</span> : 'Inactivo'}</td>
                  <td>
                    {!periodo.activo && (
                      <button type="button" disabled={guardando} onClick={() => activar(periodo.anio, periodo.tipo)}>
                        Activar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="tarjeta">
        <h2>Activar otro periodo</h2>
        <form className="formulario" onSubmit={alEnviar}>
          <label>
            Año
            <input
              type="number"
              min="2000"
              max="2100"
              value={anio}
              onChange={(evento) => setAnio(evento.target.value)}
              required
            />
          </label>
          <label>
            Periodo
            <select value={tipo} onChange={(evento) => setTipo(evento.target.value)}>
              <option value="ENERO_JUNIO">Enero–Junio</option>
              <option value="AGOSTO_DICIEMBRE">Agosto–Diciembre</option>
            </select>
          </label>
          <button type="submit" disabled={guardando}>
            Activar periodo
          </button>
        </form>
      </section>
    </>
  )
}