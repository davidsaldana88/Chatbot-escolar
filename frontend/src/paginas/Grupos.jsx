import { useState } from 'react'
import { pedir } from '../api'
import DetalleGrupo from '../componentes/DetalleGrupo'
import { useDatos } from '../useDatos'

const NOMBRES_PERIODO = { ENERO_JUNIO: 'Enero–Junio', AGOSTO_DICIEMBRE: 'Agosto–Diciembre' }
const NOMBRES_TURNO = { MATUTINO: 'Matutino', VESPERTINO: 'Vespertino' }
const NOMBRES_ESTADO = { DISPONIBLE: 'Disponible', LLENO: 'Lleno', INACTIVO: 'Inactivo' }

function FilaGrupo({ grupo, ocupado, alSeleccionar, alGuardar, seleccionado }) {
  const [cupo, setCupo] = useState(grupo.cupo ?? 0)
  const [estado, setEstado] = useState(grupo.estado)
  const cambiado = Number(cupo) !== grupo.cupo || estado !== grupo.estado

  return (
    <tr className={seleccionado ? 'fila--seleccionada' : undefined}>
      <td>
        <strong>{grupo.clave}</strong>
      </td>
      <td>{grupo.semestre}</td>
      <td>{NOMBRES_TURNO[grupo.turno] ?? grupo.turno}</td>
      <td>{grupo.materias}</td>
      <td>
        <input
          type="number"
          min="0"
          max="200"
          aria-label={`Cupo del grupo ${grupo.clave}`}
          value={cupo}
          onChange={(e) => setCupo(e.target.value)}
        />
      </td>
      <td>
        <select aria-label={`Estado del grupo ${grupo.clave}`} value={estado} onChange={(e) => setEstado(e.target.value)}>
          {Object.entries(NOMBRES_ESTADO).map(([clave, texto]) => (
            <option key={clave} value={clave}>
              {texto}
            </option>
          ))}
        </select>
      </td>
      <td className="acciones">
        <button type="button" disabled={ocupado || !cambiado} onClick={() => alGuardar(grupo.id, { cupo: Number(cupo), estado })}>
          Guardar
        </button>
        <button type="button" className="boton-secundario" onClick={() => alSeleccionar(grupo)}>
          Horarios
        </button>
      </td>
    </tr>
  )
}

export default function Grupos() {
  const periodos = useDatos('/admin/periodos')
  const [periodoElegido, setPeriodoElegido] = useState(null)
  const [seleccionado, setSeleccionado] = useState(null)
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)
  const [nuevo, setNuevo] = useState({ semestre: '', clave: '', turno: 'MATUTINO', cupo: 30 })

  const periodoId = periodoElegido ?? periodos.datos?.find((p) => p.activo)?.id ?? periodos.datos?.[0]?.id ?? null
  const periodo = periodos.datos?.find((p) => p.id === periodoId)
  const grupos = useDatos(periodoId ? `/admin/grupos?periodo_id=${periodoId}` : null)

  async function ejecutar(accion, textoExito) {
    setOcupado(true)
    setMensaje(null)
    try {
      await accion()
      setMensaje({ texto: textoExito, error: false })
      await grupos.recargar()
      return true
    } catch (e) {
      setMensaje({ texto: e.message, error: true })
      return false
    } finally {
      setOcupado(false)
    }
  }

  function guardarGrupo(id, cambios) {
    ejecutar(() => pedir(`/admin/grupos/${id}`, { metodo: 'PUT', cuerpo: cambios }), 'Grupo actualizado.')
  }

  async function crearGrupo(evento) {
    evento.preventDefault()
    const creado = await ejecutar(
      () =>
        pedir('/admin/grupos', {
          metodo: 'POST',
          cuerpo: {
            periodo_id: periodoId,
            semestre: Number(nuevo.semestre),
            clave: nuevo.clave.trim().toUpperCase(),
            turno: nuevo.turno,
            cupo: Number(nuevo.cupo),
          },
        }),
      'Grupo creado. Ábrelo con «Horarios» para agregarle materias.',
    )
    if (creado) setNuevo({ semestre: '', clave: '', turno: 'MATUTINO', cupo: 30 })
  }

  function cambiarPeriodo(valor) {
    setPeriodoElegido(Number(valor))
    setSeleccionado(null)
    setMensaje(null)
  }

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Grupos y horarios</h1>
        <p>
          Consulta los grupos de cada periodo, ajusta su cupo y estado, y edita las materias, profesores y horarios.
          Los cambios aparecen en el chatbot de inmediato. Al guardar un horario se verifica que no choquen el
          profesor, el grupo ni el salón.
        </p>
      </header>

      {periodos.error && (
        <p className="aviso aviso--error" role="alert">
          {periodos.error}
        </p>
      )}
      {periodos.datos?.length === 0 && <p className="aviso">No hay periodos escolares registrados.</p>}

      {periodoId && (
        <>
          <label className="campo-en-linea">
            Periodo
            <select value={periodoId} onChange={(e) => cambiarPeriodo(e.target.value)}>
              {periodos.datos.map((p) => (
                <option key={p.id} value={p.id}>
                  {NOMBRES_PERIODO[p.tipo]} {p.anio}
                  {p.activo ? ' (activo)' : ''}
                </option>
              ))}
            </select>
          </label>

          {mensaje && !seleccionado && (
            <p className={'aviso' + (mensaje.error ? ' aviso--error' : ' aviso--exito')} role="status">
              {mensaje.texto}
            </p>
          )}

          <section className="tarjeta">
            <h2>Grupos</h2>
            {grupos.cargando && <p className="vacio">Cargando grupos…</p>}
            {grupos.error && (
              <p className="aviso aviso--error" role="alert">
                {grupos.error}
              </p>
            )}
            {grupos.datos && (
              <div className="tabla-contenedor">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Grupo</th>
                      <th>Semestre</th>
                      <th>Turno</th>
                      <th>Materias</th>
                      <th>Cupo</th>
                      <th>Estado</th>
                      <th>
                        <span className="solo-lectores">Acciones</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {grupos.datos.map((grupo) => (
                      <FilaGrupo
                        key={`${grupo.id}-${grupo.cupo}-${grupo.estado}`}
                        grupo={grupo}
                        ocupado={ocupado}
                        seleccionado={seleccionado?.id === grupo.id}
                        alGuardar={guardarGrupo}
                        alSeleccionar={setSeleccionado}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="tarjeta">
            <h2>Crear grupo</h2>
            <form className="formulario" onSubmit={crearGrupo}>
              <label>
                Semestre
                <select value={nuevo.semestre} onChange={(e) => setNuevo({ ...nuevo, semestre: e.target.value })} required>
                  <option value="">Elige</option>
                  {periodo?.semestres_ofertados.map((numero) => (
                    <option key={numero} value={numero}>
                      {numero}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Clave (ej. M3)
                <input
                  type="text"
                  minLength="2"
                  maxLength="4"
                  value={nuevo.clave}
                  onChange={(e) => setNuevo({ ...nuevo, clave: e.target.value })}
                  required
                />
              </label>
              <label>
                Turno
                <select value={nuevo.turno} onChange={(e) => setNuevo({ ...nuevo, turno: e.target.value })}>
                  <option value="MATUTINO">Matutino</option>
                  <option value="VESPERTINO">Vespertino</option>
                </select>
              </label>
              <label>
                Cupo
                <input
                  type="number"
                  min="0"
                  max="200"
                  value={nuevo.cupo}
                  onChange={(e) => setNuevo({ ...nuevo, cupo: e.target.value })}
                  required
                />
              </label>
              <button type="submit" disabled={ocupado}>
                Crear grupo
              </button>
            </form>
          </section>

          {seleccionado && (
            <DetalleGrupo
              key={seleccionado.id}
              grupo={seleccionado}
              alCerrar={() => setSeleccionado(null)}
              alActualizar={grupos.recargar}
            />
          )}
        </>
      )}
    </>
  )
}