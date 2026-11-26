import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { borrarToken, pedir } from '../api'
import './PanelAdmin.css'

const ENLACES = [
  { ruta: '/admin', texto: 'Inicio', exacto: true },
  { ruta: '/admin/grupos', texto: 'Grupos y horarios' },
  { ruta: '/admin/materias', texto: 'Materias y profesores' },
  { ruta: '/admin/opiniones', texto: 'Opiniones' },
  { ruta: '/admin/configuracion', texto: 'Configuración' },
]

export default function PanelAdmin() {
  const navegar = useNavigate()

  async function cerrarSesion() {
    try {
      await pedir('/auth/salir', { metodo: 'POST' })
    } catch {
      // Si el servidor ya no reconoce la sesión, igual se cierra aquí.
    }
    borrarToken()
    navegar('/admin/login', { replace: true })
  }

  return (
    <div className="panel">
      <aside className="panel__menu">
        <div className="panel__marca">
          <strong>Chatbot escolar</strong>
          <span>Administración</span>
        </div>
        <nav aria-label="Secciones">
          {ENLACES.map((enlace) => (
            <NavLink key={enlace.ruta} to={enlace.ruta} end={enlace.exacto}>
              {enlace.texto}
            </NavLink>
          ))}
        </nav>
        <NavLink to="/" className="panel__chat">
          Ver el chatbot
        </NavLink>
        <button type="button" className="panel__salir" onClick={cerrarSesion}>
          Cerrar sesión
        </button>
      </aside>
      <main className="panel__contenido">
        <Outlet />
      </main>
    </div>
  )
}