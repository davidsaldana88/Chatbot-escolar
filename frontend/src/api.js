// Llamadas al backend. Vite redirige /api/... hacia FastAPI (ver vite.config.js).
let tokenEnMemoria = null

export function leerToken() {
  if (tokenEnMemoria) return tokenEnMemoria
  try {
    tokenEnMemoria = sessionStorage.getItem('token_admin')
  } catch {
    // Sin almacenamiento disponible: solo se usa la memoria.
  }
  return tokenEnMemoria
}

export function guardarToken(token) {
  tokenEnMemoria = token
  try {
    sessionStorage.setItem('token_admin', token)
  } catch {
    // Sin almacenamiento disponible: solo se usa la memoria.
  }
}

export function borrarToken() {
  tokenEnMemoria = null
  try {
    sessionStorage.removeItem('token_admin')
  } catch {
    // Sin almacenamiento disponible.
  }
}

export async function pedir(ruta, { metodo = 'GET', cuerpo } = {}) {
  const cabeceras = { 'Content-Type': 'application/json' }
  const token = leerToken()
  if (token) cabeceras.Authorization = `Bearer ${token}`
  let respuesta
  try {
    respuesta = await fetch(`/api${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    })
  } catch {
    throw new Error('No pude conectar con el servidor. Verifica que el backend esté encendido.')
  }
  let datos = null
  try {
    datos = await respuesta.json()
  } catch {
    // La respuesta no trae cuerpo JSON.
  }
  if (respuesta.status === 401 && ruta !== '/auth/login') {
    // La sesión expiró (o el servidor se reinició): volver al login.
    borrarToken()
    window.location.assign('/admin/login')
    throw new Error('Tu sesión expiró. Inicia sesión de nuevo.')
  }
  if (!respuesta.ok) {
    const detalle = typeof datos?.detail === 'string' ? datos.detail : 'No se pudo completar la solicitud'
    throw new Error(detalle)
  }
  return datos
}