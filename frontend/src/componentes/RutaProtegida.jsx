import { Navigate } from 'react-router-dom'
import { leerToken } from '../api'

export default function RutaProtegida({ children }) {
  if (!leerToken()) return <Navigate to="/admin/login" replace />
  return children
}