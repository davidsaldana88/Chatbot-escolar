import { useState } from 'react'
import { pedir } from '../api'
import { useDatos } from '../useDatos'

const DIAS = [
  ['LUNES', 'Lunes'],
  ['MARTES', 'Martes'],
  ['MIERCOLES', 'Miércoles'],
  ['JUEVES', 'Jueves'],
  ['VIERNES', 'Viernes'],
]
const SALONES = ['E1', 'E2', 'E3', 'E4', 'E5', 'L1', 'L2', 'L3', 'L4', 'L5']

function CamposHorario({ valor, alCambiar }) {
  function cambiar(campo, nuevo) {
    alCambiar({ ...valor, [campo]: nuevo })
  }
  return (
    <>
      <select aria-label="Día" value={valor.dia_semana} onChange={(e) => cambiar('dia_semana', e.target.value)}>
        {DIAS.map(([clave, texto]) => (
          <option key={clave} value={clave}>
            {texto}
          </option>
        ))}
      </select>
      <input
        type="time"
        aria-label="Hora de inicio"
        value={valor.hora_inicio}
        onChange={(e) => cambiar('hora_inicio', e.target.value)}
      />
      <input
        type="time"
        aria-label="Hora de fin"
        value={valor.hora_fin}
        onChange={(e) => cambiar('hora_fin', e.target.value)}
      />
      <select aria-label="Salón" value={valor.salon} onChange={(e) => cambiar('salon', e.target.value)}>
        {SALONES.map((salon) => (
          <option key={salon} value={salon}>
            {salon}
          </option>
        ))}
      </select>
    </>
  )
}

function FilaHorario({ horario, ocupado, ejecutar }) {
  const [valor, setValor] = useState({
    dia_semana: horario.dia_semana,
    hora_inicio: horario.hora_inicio,
    hora_fin: horario.hora_fin,
    salon: horario.salon,
  })
  const cambiado = Object.keys(valor).some((campo) => valor[campo] !== horario[campo])

  function guardar() {
    ejecutar(() => pedir(`/admin/horarios/${horario.id}`, { metodo: 'PUT', cuerpo: valor }), 'Horario guardado.')
  }

  function eliminar() {
    if (!window.confirm('¿Eliminar este bloque de horario?')) return
    ejecutar(() => pedir(`/admin/horarios/${horario.id}`, { metodo: 'DELETE' }), 'Horario eliminado.')
  }

  return (
    <div className="fila-horario">
      <CamposHorario valor={valor} alCambiar={setValor} />
      <button type="button" disabled={ocupado || !cambiado} onClick={guardar}>
        Guardar
      </button>
      <button type="button" className="boton-secundario" disabled={ocupado} onClick={eliminar}>
        Eliminar
      </button>
    </div>
  )
}

function FilaNueva({ asignacionId, salonInicial, ocupado, ejecutar }) {
  const [valor, setValor] = useState({
    dia_semana: 'LUNES',
    hora_inicio: '07:00',
    hora_fin: '08:00',
    salon: salonInicial,
  })

  function agregar() {
    ejecutar(
      () => pedir('/admin/horarios', { metodo: 'POST', cuerpo: { asignacion_id: asignacionId, ...valor } }),
      'Horario agregado.',
    )
  }

  return (
    <div className="fila-horario fila-horario--nueva">
      <CamposHorario valor={valor} alCambiar={setValor} />
      <button type="button" className="boton-secundario" disabled={ocupado} onClick={agregar}>
        Agregar bloque
      </button>
    </div>
  )
}

export default function DetalleGrupo({ grupo, alCerrar, alActualizar }) {
  const asignaciones = useDatos(`/admin/grupos/${grupo.id}/asignaciones`)
  const profesores = useDatos('/admin/profesores')
  const materias = useDatos('/admin/materias')
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)
  const [materiaNueva, setMateriaNueva] = useState('')
  const [profesorNuevo, setProfesorNuevo] = useState('')

  const profesoresActivos = (profesores.datos ?? []).filter((p) => p.activo)
  const lista = asignaciones.datos ?? []
  const salonInicial = lista.flatMap((a) => a.horarios)[0]?.salon ?? 'E1'
  const materiasLibres = (materias.datos ?? []).filter(
    (m) => m.semestre === grupo.semestre && !lista.some((a) => a.materia_id === m.id),
  )

  async function ejecutar(accion, textoExito) {
    setOcupado(true)
    setMensaje(null)
    try {
      await accion()
      setMensaje({ texto: textoExito, error: false })
      await asignaciones.recargar()
      alActualizar?.()
      return true
    } catch (e) {
      setMensaje({ texto: e.message, error: true })
      return false
    } finally {
      setOcupado(false)
    }
  }

  function cambiarProfesor(asignacionId, profesorId) {
    ejecutar(
      () => pedir(`/admin/asignaciones/${asignacionId}`, { metodo: 'PUT', cuerpo: { profesor_id: Number(profesorId) } }),
      'Profesor actualizado.',
    )
  }

  async function agregarMateria(evento) {
    evento.preventDefault()
    const agregada = await ejecutar(
      () =>
        pedir('/admin/asignaciones', {
          metodo: 'POST',
          cuerpo: { grupo_id: grupo.id, materia_id: Number(materiaNueva), profesor_id: Number(profesorNuevo) },
        }),
      'Materia agregada al grupo.',
    )
    if (agregada) {
      setMateriaNueva('')
      setProfesorNuevo('')
    }
  }

  return (
    <section className="detalle" aria-label={`Detalle del grupo ${grupo.clave}`}>
      <div className="detalle__cabecera">
        <h2>
          Grupo {grupo.clave} · Semestre {grupo.semestre}
        </h2>
        <button type="button" className="boton-secundario" onClick={alCerrar}>
          Cerrar
        </button>
      </div>

      {mensaje && (
        <p className={'aviso' + (mensaje.error ? ' aviso--error' : ' aviso--exito')} role="status">
          {mensaje.texto}
        </p>
      )}
      {asignaciones.cargando && <p className="vacio">Cargando materias…</p>}
      {asignaciones.error && (
        <p className="aviso aviso--error" role="alert">
          {asignaciones.error}
        </p>
      )}

      {lista.map((asignacion) => (
        <article key={asignacion.id} className="tarjeta">
          <div className="asignacion__cabecera">
            <h3>{asignacion.materia}</h3>
            <label className="campo-en-linea">
              Profesor
              <select
                value={asignacion.profesor_id}
                disabled={ocupado}
                onChange={(e) => cambiarProfesor(asignacion.id, e.target.value)}
              >
                {profesoresActivos.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
                {!profesoresActivos.some((p) => p.id === asignacion.profesor_id) && (
                  <option value={asignacion.profesor_id}>{asignacion.profesor}</option>
                )}
              </select>
            </label>
          </div>
          {asignacion.horarios.length === 0 && <p className="vacio">Esta materia todavía no tiene horario.</p>}
          {asignacion.horarios.map((horario) => (
            <FilaHorario key={horario.id} horario={horario} ocupado={ocupado} ejecutar={ejecutar} />
          ))}
          <FilaNueva asignacionId={asignacion.id} salonInicial={salonInicial} ocupado={ocupado} ejecutar={ejecutar} />
        </article>
      ))}

      {materiasLibres.length > 0 && (
        <form className="tarjeta formulario" onSubmit={agregarMateria}>
          <label>
            Materia del semestre {grupo.semestre} sin asignar
            <select value={materiaNueva} onChange={(e) => setMateriaNueva(e.target.value)} required>
              <option value="">Elige una materia</option>
              {materiasLibres.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nombre}
                </option>
              ))}
            </select>
          </label>
          <label>
            Profesor
            <select value={profesorNuevo} onChange={(e) => setProfesorNuevo(e.target.value)} required>
              <option value="">Elige un profesor</option>
              {profesoresActivos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={ocupado}>
            Agregar materia
          </button>
        </form>
      )}
    </section>
  )
}