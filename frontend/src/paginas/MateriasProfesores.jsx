import { useState } from 'react'
import { pedir } from '../api'
import { useDatos } from '../useDatos'

const PESTANAS = [
  ['materias', 'Materias'],
  ['profesores', 'Profesores'],
]
const SEMESTRES = Array.from({ length: 10 }, (_, i) => i + 1)

// Ejecuta una acción contra el backend, muestra el resultado y recarga la lista.
function useAcciones(recargar) {
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)

  async function ejecutar(accion, textoExito) {
    setOcupado(true)
    setMensaje(null)
    try {
      await accion()
      setMensaje({ texto: textoExito, error: false })
      await recargar()
      return true
    } catch (e) {
      setMensaje({ texto: e.message, error: true })
      return false
    } finally {
      setOcupado(false)
    }
  }

  return { mensaje, ocupado, ejecutar }
}

function Mensaje({ mensaje }) {
  if (!mensaje) return null
  return (
    <p className={'aviso' + (mensaje.error ? ' aviso--error' : ' aviso--exito')} role="status">
      {mensaje.texto}
    </p>
  )
}

function FilaMateria({ materia, ocupado, alGuardar }) {
  const [nombre, setNombre] = useState(materia.nombre)
  const [semestre, setSemestre] = useState(materia.semestre)
  const cambiado = nombre.trim() !== materia.nombre || Number(semestre) !== materia.semestre

  return (
    <tr>
      <td>
        <select
          aria-label={`Semestre de ${materia.nombre}`}
          value={semestre}
          onChange={(e) => setSemestre(e.target.value)}
        >
          {SEMESTRES.map((numero) => (
            <option key={numero} value={numero}>
              {numero}
            </option>
          ))}
        </select>
      </td>
      <td>
        <input
          type="text"
          aria-label={`Nombre de la materia ${materia.nombre}`}
          value={nombre}
          minLength={3}
          maxLength={120}
          onChange={(e) => setNombre(e.target.value)}
        />
      </td>
      <td>{materia.clave ?? '—'}</td>
      <td>
        <button
          type="button"
          disabled={ocupado || !cambiado || nombre.trim().length < 3}
          onClick={() => alGuardar(materia.id, { nombre: nombre.trim(), semestre: Number(semestre) })}
        >
          Guardar
        </button>
      </td>
    </tr>
  )
}

function PanelMaterias() {
  const { datos, error, cargando, recargar } = useDatos('/admin/materias')
  const { mensaje, ocupado, ejecutar } = useAcciones(recargar)
  const [filtro, setFiltro] = useState('')
  const [nueva, setNueva] = useState({ semestre: '', nombre: '', clave: '', descripcion: '' })

  const visibles = (datos ?? []).filter((m) => !filtro || m.semestre === Number(filtro))

  function guardar(id, cambios) {
    ejecutar(() => pedir(`/admin/materias/${id}`, { metodo: 'PUT', cuerpo: cambios }), 'Materia actualizada.')
  }

  async function crear(evento) {
    evento.preventDefault()
    const creada = await ejecutar(
      () =>
        pedir('/admin/materias', {
          metodo: 'POST',
          cuerpo: {
            semestre: Number(nueva.semestre),
            nombre: nueva.nombre.trim(),
            clave: nueva.clave.trim() || null,
            descripcion: nueva.descripcion.trim() || null,
          },
        }),
      'Materia creada.',
    )
    if (creada) setNueva({ semestre: '', nombre: '', clave: '', descripcion: '' })
  }

  return (
    <>
      <Mensaje mensaje={mensaje} />
      <section className="tarjeta">
        <h2>Materias de la retícula</h2>
        <label className="campo-en-linea">
          Semestre
          <select value={filtro} onChange={(e) => setFiltro(e.target.value)}>
            <option value="">Todos</option>
            {SEMESTRES.map((numero) => (
              <option key={numero} value={numero}>
                {numero}
              </option>
            ))}
          </select>
        </label>
        {cargando && <p className="vacio">Cargando…</p>}
        {error && (
          <p className="aviso aviso--error" role="alert">
            {error}
          </p>
        )}
        {datos && (
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Semestre</th>
                  <th>Nombre</th>
                  <th>Clave</th>
                  <th>
                    <span className="solo-lectores">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visibles.map((materia) => (
                  <FilaMateria
                    key={`${materia.id}-${materia.nombre}-${materia.semestre}`}
                    materia={materia}
                    ocupado={ocupado}
                    alGuardar={guardar}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="vacio">
          El semestre de una materia solo se puede cambiar mientras no esté asignada a ningún grupo.
        </p>
      </section>

      <section className="tarjeta">
        <h2>Agregar materia</h2>
        <form className="formulario" onSubmit={crear}>
          <label>
            Semestre
            <select value={nueva.semestre} onChange={(e) => setNueva({ ...nueva, semestre: e.target.value })} required>
              <option value="">Elige</option>
              {SEMESTRES.map((numero) => (
                <option key={numero} value={numero}>
                  {numero}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nombre
            <input
              type="text"
              minLength={3}
              maxLength={120}
              value={nueva.nombre}
              onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })}
              required
            />
          </label>
          <label>
            Clave (opcional)
            <input
              type="text"
              maxLength={20}
              value={nueva.clave}
              onChange={(e) => setNueva({ ...nueva, clave: e.target.value })}
            />
          </label>
          <button type="submit" disabled={ocupado}>
            Agregar materia
          </button>
        </form>
      </section>
    </>
  )
}

function FilaProfesor({ profesor, ocupado, alGuardar }) {
  const [nombre, setNombre] = useState(profesor.nombre)
  const [correo, setCorreo] = useState(profesor.correo ?? '')
  const [area, setArea] = useState(profesor.area ?? '')
  const [activo, setActivo] = useState(!!profesor.activo)
  const cambiado =
    nombre.trim() !== profesor.nombre ||
    correo.trim() !== (profesor.correo ?? '') ||
    area.trim() !== (profesor.area ?? '') ||
    activo !== !!profesor.activo

  return (
    <tr>
      <td>
        <input
          type="text"
          aria-label={`Nombre de ${profesor.nombre}`}
          value={nombre}
          minLength={3}
          maxLength={120}
          onChange={(e) => setNombre(e.target.value)}
        />
      </td>
      <td>
        <input
          type="email"
          aria-label={`Correo de ${profesor.nombre}`}
          value={correo}
          maxLength={120}
          onChange={(e) => setCorreo(e.target.value)}
        />
      </td>
      <td>
        <input
          type="text"
          aria-label={`Área de ${profesor.nombre}`}
          value={area}
          maxLength={80}
          onChange={(e) => setArea(e.target.value)}
        />
      </td>
      <td>{profesor.materias}</td>
      <td>
        <label className="campo-en-linea">
          <input type="checkbox" checked={activo} onChange={(e) => setActivo(e.target.checked)} />
          Activo
        </label>
      </td>
      <td>
        <button
          type="button"
          disabled={ocupado || !cambiado || nombre.trim().length < 3}
          onClick={() =>
            alGuardar(profesor.id, { nombre: nombre.trim(), correo: correo.trim(), area: area.trim(), activo })
          }
        >
          Guardar
        </button>
      </td>
    </tr>
  )
}

function PanelProfesores() {
  const { datos, error, cargando, recargar } = useDatos('/admin/profesores')
  const { mensaje, ocupado, ejecutar } = useAcciones(recargar)
  const [nuevo, setNuevo] = useState({ nombre: '', correo: '', area: '' })

  function guardar(id, cambios) {
    ejecutar(() => pedir(`/admin/profesores/${id}`, { metodo: 'PUT', cuerpo: cambios }), 'Profesor actualizado.')
  }

  async function crear(evento) {
    evento.preventDefault()
    const creado = await ejecutar(
      () =>
        pedir('/admin/profesores', {
          metodo: 'POST',
          cuerpo: {
            nombre: nuevo.nombre.trim(),
            correo: nuevo.correo.trim() || null,
            area: nuevo.area.trim() || null,
          },
        }),
      'Profesor agregado.',
    )
    if (creado) setNuevo({ nombre: '', correo: '', area: '' })
  }

  return (
    <>
      <Mensaje mensaje={mensaje} />
      <section className="tarjeta">
        <h2>Profesores</h2>
        {cargando && <p className="vacio">Cargando…</p>}
        {error && (
          <p className="aviso aviso--error" role="alert">
            {error}
          </p>
        )}
        {datos && (
          <div className="tabla-contenedor">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Correo</th>
                  <th>Área</th>
                  <th>Materias</th>
                  <th>Estado</th>
                  <th>
                    <span className="solo-lectores">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {datos.map((profesor) => (
                  <FilaProfesor
                    key={`${profesor.id}-${profesor.nombre}-${profesor.correo}-${profesor.area}-${profesor.activo}`}
                    profesor={profesor}
                    ocupado={ocupado}
                    alGuardar={guardar}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="vacio">
          Un profesor inactivo ya no aparece para nuevas asignaciones ni para opiniones, pero conserva las materias
          que ya tenía asignadas.
        </p>
      </section>

      <section className="tarjeta">
        <h2>Agregar profesor</h2>
        <form className="formulario" onSubmit={crear}>
          <label>
            Nombre
            <input
              type="text"
              minLength={3}
              maxLength={120}
              value={nuevo.nombre}
              onChange={(e) => setNuevo({ ...nuevo, nombre: e.target.value })}
              required
            />
          </label>
          <label>
            Correo (opcional)
            <input
              type="email"
              maxLength={120}
              value={nuevo.correo}
              onChange={(e) => setNuevo({ ...nuevo, correo: e.target.value })}
            />
          </label>
          <label>
            Área (opcional)
            <input
              type="text"
              maxLength={80}
              value={nuevo.area}
              onChange={(e) => setNuevo({ ...nuevo, area: e.target.value })}
            />
          </label>
          <button type="submit" disabled={ocupado}>
            Agregar profesor
          </button>
        </form>
      </section>
    </>
  )
}

export default function MateriasProfesores() {
  const [pestana, setPestana] = useState('materias')

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Materias y profesores</h1>
        <p>
          Administra el catálogo: las materias de la retícula y los profesores. Para asignar una materia a un grupo y a
          un profesor, usa la sección Grupos y horarios.
        </p>
      </header>

      <div className="pestanas" role="tablist" aria-label="Catálogo">
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

      {pestana === 'materias' && <PanelMaterias key="materias" />}
      {pestana === 'profesores' && <PanelProfesores key="profesores" />}
    </>
  )
}