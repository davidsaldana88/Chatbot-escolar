import { useState } from 'react'
import { Link } from 'react-router-dom'
import { pedir } from '../api'
import { useDatos } from '../useDatos'
import './FormularioOpinion.css'

const VACIO = { materiaId: '', profesorId: '', calificacion: 0, comentario: '', alias: '' }

// Se vuelve a montar cada vez que cambia la materia (por la propiedad key), para no mostrar
// profesores de la materia anterior mientras cargan los nuevos.
function SelectorProfesor({ materiaId, valor, alCambiar }) {
  const { datos, error, cargando } = useDatos(`/materias/${materiaId}/profesores`)
  return (
    <label>
      Profesor
      <select value={valor} onChange={(e) => alCambiar(e.target.value)} required disabled={cargando || !!error}>
        <option value="">{cargando ? 'Cargando…' : 'Elige un profesor'}</option>
        {(datos ?? []).map((profesor) => (
          <option key={profesor.id} value={profesor.id}>
            {profesor.nombre}
          </option>
        ))}
      </select>
      {error && <span className="opinion__error">{error}</span>}
    </label>
  )
}

export default function FormularioOpinion() {
  const materias = useDatos('/materias')
  const [formulario, setFormulario] = useState(VACIO)
  const [resultado, setResultado] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const porSemestre = {}
  for (const materia of materias.datos ?? []) {
    ;(porSemestre[materia.semestre] ??= []).push(materia)
  }

  function cambiar(campo, valor) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  function cambiarMateria(valor) {
    setFormulario((actual) => ({ ...actual, materiaId: valor, profesorId: '' }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setEnviando(true)
    setResultado(null)
    try {
      const respuesta = await pedir('/opiniones', {
        metodo: 'POST',
        cuerpo: {
          materia_id: Number(formulario.materiaId),
          profesor_id: Number(formulario.profesorId),
          calificacion: formulario.calificacion,
          comentario: formulario.comentario.trim(),
          autor_alias: formulario.alias.trim() || null,
        },
      })
      setResultado({ texto: respuesta.mensaje, error: false })
      setFormulario(VACIO)
    } catch (e) {
      setResultado({ texto: e.message, error: true })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="opinion">
      <Link to="/" className="opinion__volver">
        ← Volver al chatbot
      </Link>
      <h1>Deja tu opinión</h1>
      <p className="opinion__intro">
        Cuéntales a otros alumnos cómo fue tu experiencia con una materia y su profesor. Tu opinión se publica después
        de que un administrador la revise.
      </p>

      {resultado && (
        <p className={'opinion__aviso' + (resultado.error ? ' opinion__aviso--error' : '')} role="status">
          {resultado.texto}
        </p>
      )}
      {materias.error && (
        <p className="opinion__aviso opinion__aviso--error" role="alert">
          {materias.error}
        </p>
      )}

      <form className="opinion__formulario" onSubmit={enviar}>
        <label>
          Materia
          <select value={formulario.materiaId} onChange={(e) => cambiarMateria(e.target.value)} required>
            <option value="">{materias.cargando ? 'Cargando…' : 'Elige una materia'}</option>
            {Object.entries(porSemestre).map(([semestre, lista]) => (
              <optgroup key={semestre} label={`Semestre ${semestre}`}>
                {lista.map((materia) => (
                  <option key={materia.id} value={materia.id}>
                    {materia.nombre}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>

        {formulario.materiaId && (
          <SelectorProfesor
            key={formulario.materiaId}
            materiaId={formulario.materiaId}
            valor={formulario.profesorId}
            alCambiar={(valor) => cambiar('profesorId', valor)}
          />
        )}

        <fieldset className="opinion__calificacion">
          <legend>Calificación (1 = muy mala, 5 = excelente)</legend>
          <div>
            {[1, 2, 3, 4, 5].map((numero) => (
              <label key={numero}>
                <input
                  type="radio"
                  name="calificacion"
                  value={numero}
                  checked={formulario.calificacion === numero}
                  onChange={() => cambiar('calificacion', numero)}
                  required
                />
                <span>{numero}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <label>
          Comentario
          <textarea
            value={formulario.comentario}
            onChange={(e) => cambiar('comentario', e.target.value)}
            minLength={5}
            maxLength={500}
            rows={5}
            required
          />
          <span className="opinion__contador">{formulario.comentario.length}/500</span>
        </label>

        <label>
          Nombre o alias (opcional)
          <input
            type="text"
            value={formulario.alias}
            onChange={(e) => cambiar('alias', e.target.value)}
            maxLength={40}
            placeholder="Si lo dejas vacío, se publica como Anónimo"
          />
        </label>

        <button type="submit" disabled={enviando}>
          {enviando ? 'Enviando…' : 'Enviar opinión'}
        </button>
      </form>
    </main>
  )
}