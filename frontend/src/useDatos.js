import { useCallback, useEffect, useState } from 'react'
import { pedir } from './api'

// Carga datos de una ruta del backend y expone estado de carga, error y recarga.
// Si la ruta es null, todavía no se carga nada (útil cuando depende de otro dato).
export function useDatos(ruta) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(true)

  const recargar = useCallback(async () => {
    if (!ruta) return
    setError(null)
    try {
      setDatos(await pedir(ruta))
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }, [ruta])

  useEffect(() => {
    recargar()
  }, [recargar])

  return { datos, error, cargando, recargar }
}