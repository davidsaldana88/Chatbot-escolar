import { useDatos } from '../useDatos'

const NOMBRES_PERIODO = { ENERO_JUNIO: 'Enero–Junio', AGOSTO_DICIEMBRE: 'Agosto–Diciembre' }

const NOMBRES_INTENCION = {
  SALUDO: 'Saludos',
  DESPEDIDA: 'Despedidas',
  AYUDA: 'Ayuda',
  PERIODO: 'Periodo',
  GRUPOS: 'Grupos',
  MATERIAS: 'Materias',
  PROFESORES: 'Profesores',
  HORARIOS: 'Horarios',
  OPINIONES: 'Opiniones',
  NO_ENTENDIDO: 'No entendidas',
}

function Indicador({ titulo, valor, destacado }) {
  return (
    <div className={'indicador' + (destacado ? ' indicador--destacado' : '')}>
      <span className="indicador__valor">{valor}</span>
      <span className="indicador__titulo">{titulo}</span>
    </div>
  )
}

export default function Inicio() {
  const { datos, error, cargando, recargar } = useDatos('/admin/estadisticas')

  if (cargando) return <p className="aviso">Cargando estadísticas…</p>
  if (error) {
    return (
      <div className="aviso aviso--error" role="alert">
        <p>{error}</p>
        <button type="button" onClick={recargar}>
          Reintentar
        </button>
      </div>
    )
  }

  const { periodo_activo: periodo, totales, consultas_por_intencion: intenciones } = datos
  const maximo = Math.max(1, ...intenciones.map((i) => i.total))

  return (
    <>
      <header className="encabezado-pagina">
        <h1>Inicio</h1>
        <p>
          {periodo
            ? `Periodo activo: ${NOMBRES_PERIODO[periodo.tipo]} ${periodo.anio} · Semestres ofertados: ${periodo.semestres_ofertados.join(', ')}`
            : 'No hay un periodo activo. Configúralo en la sección Configuración.'}
        </p>
      </header>

      <section className="indicadores" aria-label="Resumen">
        <Indicador titulo="Grupos activos" valor={totales.grupos_activos} />
        <Indicador titulo="Materias" valor={totales.materias} />
        <Indicador titulo="Profesores" valor={totales.profesores} />
        <Indicador
          titulo="Opiniones pendientes"
          valor={totales.opiniones_pendientes}
          destacado={totales.opiniones_pendientes > 0}
        />
        <Indicador titulo="Opiniones publicadas" valor={totales.opiniones_publicadas} />
        <Indicador titulo="Conversaciones" valor={totales.sesiones_chat} />
        <Indicador titulo="Mensajes de estudiantes" valor={totales.mensajes_estudiantes} />
      </section>

      <div className="columnas">
        <section className="tarjeta">
          <h2>Consultas por tema</h2>
          {intenciones.length === 0 ? (
            <p className="vacio">Todavía no hay conversaciones.</p>
          ) : (
            <ul className="barras">
              {intenciones.map((fila) => (
                <li key={fila.intencion}>
                  <span className="barras__nombre">{NOMBRES_INTENCION[fila.intencion] ?? fila.intencion}</span>
                  <span className="barras__pista">
                    <span className="barras__relleno" style={{ width: `${(fila.total / maximo) * 100}%` }} />
                  </span>
                  <span className="barras__valor">{fila.total}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="tarjeta">
          <h2>Preguntas frecuentes</h2>
          {datos.preguntas_frecuentes.length === 0 ? (
            <p className="vacio">Todavía no hay preguntas.</p>
          ) : (
            <ol className="lista-simple">
              {datos.preguntas_frecuentes.map((fila) => (
                <li key={fila.pregunta}>
                  <span>{fila.pregunta}</span>
                  <span className="etiqueta">{fila.veces}×</span>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      <section className="tarjeta">
        <h2>Mensajes por día</h2>
        {datos.mensajes_por_dia.length === 0 ? (
          <p className="vacio">Todavía no hay mensajes.</p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Día</th>
                <th>Mensajes</th>
              </tr>
            </thead>
            <tbody>
              {datos.mensajes_por_dia.map((fila) => (
                <tr key={fila.dia}>
                  <td>{fila.dia}</td>
                  <td>{fila.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  )
}