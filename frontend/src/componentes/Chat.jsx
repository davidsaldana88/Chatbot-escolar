import { useEffect, useRef, useState } from 'react'
import './Chat.css'
import { Link } from 'react-router-dom'

const MENSAJE_INICIAL = {
  remitente: 'CHATBOT',
  texto:
    '¡Hola! Soy el asistente de inscripciones de Ingeniería en Sistemas Inteligentes. ' +
    'Pregúntame por grupos, materias, profesores, horarios u opiniones.',
  sugerencias: ['Grupos disponibles', 'Materias', 'Profesores', 'Horarios'],
}

function leerSesion() {
  try {
    return sessionStorage.getItem('sesion_chat')
  } catch {
    return null
  }
}

function guardarSesion(valor) {
  try {
    sessionStorage.setItem('sesion_chat', valor)
  } catch {
    // Sin almacenamiento disponible: el chat sigue funcionando sin recordar la sesión.
  }
}

export default function Chat() {
  const [mensajes, setMensajes] = useState([MENSAJE_INICIAL])
  const [entrada, setEntrada] = useState('')
  const [cargando, setCargando] = useState(false)
  const sesion = useRef(leerSesion())
  const finDeMensajes = useRef(null)

  useEffect(() => {
    finDeMensajes.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes, cargando])

  async function enviarMensaje(texto) {
    const limpio = texto.trim()
    if (!limpio || cargando) return
    setMensajes((actuales) => [...actuales, { remitente: 'ESTUDIANTE', texto: limpio }])
    setEntrada('')
    setCargando(true)
    try {
      const respuesta = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: limpio, sesion: sesion.current }),
      })
      if (!respuesta.ok) throw new Error('Respuesta no válida')
      const datos = await respuesta.json()
      sesion.current = datos.sesion
      guardarSesion(datos.sesion)
      setMensajes((actuales) => [
        ...actuales,
        { remitente: 'CHATBOT', texto: datos.respuesta, sugerencias: datos.sugerencias },
      ])
    } catch {
      setMensajes((actuales) => [
        ...actuales,
        {
          remitente: 'CHATBOT',
          error: true,
          texto: 'No pude conectar con el servidor. Verifica que el backend esté encendido.',
        },
      ])
    } finally {
      setCargando(false)
    }
  }

  function alEnviar(evento) {
    evento.preventDefault()
    enviarMensaje(entrada)
  }

  const indiceUltimo = mensajes.length - 1

  return (
    <main className="chat">
      <header className="chat__encabezado">
        <h1>Asistente de inscripciones</h1>
        <p>Ingeniería en Sistemas Inteligentes</p>
                <Link to="/opiniones" className="chat__enlace">
          Dejar una opinión
        </Link>
      </header>

      <div className="chat__mensajes" aria-live="polite">
        {mensajes.map((mensaje, indice) => (
          <div
            key={indice}
            className={
              'burbuja ' +
              (mensaje.remitente === 'ESTUDIANTE' ? 'burbuja--estudiante' : 'burbuja--chatbot') +
              (mensaje.error ? ' burbuja--error' : '')
            }
          >
            {mensaje.texto}
            {mensaje.sugerencias?.length > 0 && indice === indiceUltimo && (
              <div className="sugerencias">
                {mensaje.sugerencias.map((sugerencia) => (
                  <button
                    key={sugerencia}
                    type="button"
                    disabled={cargando}
                    onClick={() => enviarMensaje(sugerencia)}
                  >
                    {sugerencia}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {cargando && <div className="escribiendo">Escribiendo…</div>}
        <div ref={finDeMensajes} />
      </div>

      <form className="chat__formulario" onSubmit={alEnviar}>
        <input
          type="text"
          value={entrada}
          onChange={(evento) => setEntrada(evento.target.value)}
          placeholder="Escribe tu pregunta…"
          maxLength={500}
          aria-label="Mensaje"
        />
        <button type="submit" disabled={cargando || !entrada.trim()}>
          Enviar
        </button>
      </form>
    </main>
  )
}