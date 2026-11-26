import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { guardarToken, leerToken, pedir } from '../api'
import './Login.css'

export default function Login() {
  const navegar = useNavigate()
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (leerToken()) return <Navigate to="/admin" replace />

  async function entrar(evento) {
    evento.preventDefault()
    setError('')
    setEnviando(true)
    try {
      const datos = await pedir('/auth/login', { metodo: 'POST', cuerpo: { usuario, clave } })
      guardarToken(datos.token)
      navegar('/admin', { replace: true })
    } catch (e) {
      setError(e.message)
      setClave('')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <form className="login__tarjeta" onSubmit={entrar}>
        <h1>Administración</h1>
        <p>Inicia sesión para gestionar grupos, horarios y opiniones.</p>
        <label>
          Usuario
          <input value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="username" maxLength={60} required autoFocus />
        </label>
        <label>
          Contraseña
          <input type="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="current-password" maxLength={100} required />
        </label>
        {error && <p className="login__error" role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</button>
        <Link to="/">Volver al chatbot</Link>
      </form>
    </div>
  )
}