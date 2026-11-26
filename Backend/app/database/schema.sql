PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS programas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS semestres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL UNIQUE CHECK (numero BETWEEN 1 AND 10),
    nombre TEXT
);

CREATE TABLE IF NOT EXISTS periodos_escolares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anio INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ENERO_JUNIO', 'AGOSTO_DICIEMBRE')),
    fecha_inicio TEXT,
    fecha_fin TEXT,
    activo INTEGER NOT NULL DEFAULT 0 CHECK (activo IN (0, 1)),
    UNIQUE (anio, tipo)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_un_solo_periodo_activo
ON periodos_escolares(activo)
WHERE activo = 1;

CREATE TABLE IF NOT EXISTS grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    programa_id INTEGER NOT NULL,
    semestre_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    clave TEXT NOT NULL,
    turno TEXT,
    cupo INTEGER CHECK (cupo IS NULL OR cupo >= 0),
    estado TEXT NOT NULL DEFAULT 'DISPONIBLE'
        CHECK (estado IN ('DISPONIBLE', 'LLENO', 'INACTIVO')),
    FOREIGN KEY (programa_id) REFERENCES programas(id),
    FOREIGN KEY (semestre_id) REFERENCES semestres(id),
    FOREIGN KEY (periodo_id) REFERENCES periodos_escolares(id),
    UNIQUE (periodo_id, semestre_id, clave)
);

CREATE TABLE IF NOT EXISTS materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    programa_id INTEGER NOT NULL,
    semestre_id INTEGER NOT NULL,
    clave TEXT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    FOREIGN KEY (programa_id) REFERENCES programas(id),
    FOREIGN KEY (semestre_id) REFERENCES semestres(id),
    UNIQUE (programa_id, clave)
);

CREATE TABLE IF NOT EXISTS profesores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT,
    area TEXT,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS asignaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_id INTEGER NOT NULL,
    materia_id INTEGER NOT NULL,
    profesor_id INTEGER NOT NULL,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materias(id),
    FOREIGN KEY (profesor_id) REFERENCES profesores(id),
    UNIQUE (grupo_id, materia_id)
);

CREATE TABLE IF NOT EXISTS horarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asignacion_id INTEGER NOT NULL,
    dia_semana TEXT NOT NULL CHECK (
        dia_semana IN ('LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO')
    ),
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT NOT NULL,
    salon TEXT,
    FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id) ON DELETE CASCADE,
    CHECK (hora_inicio < hora_fin)
);

CREATE TABLE IF NOT EXISTS opiniones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL,
    profesor_id INTEGER NOT NULL,
    grupo_id INTEGER,
    periodo_id INTEGER,
    autor_alias TEXT,
    calificacion INTEGER NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
    comentario TEXT NOT NULL,
    fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'PUBLICADA', 'RECHAZADA')),
    FOREIGN KEY (materia_id) REFERENCES materias(id),
    FOREIGN KEY (profesor_id) REFERENCES profesores(id),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id),
    FOREIGN KEY (periodo_id) REFERENCES periodos_escolares(id)
);

CREATE TABLE IF NOT EXISTS sesiones_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave_sesion TEXT NOT NULL UNIQUE,
    fecha_inicio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    canal TEXT NOT NULL DEFAULT 'WEB',
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'CERRADA'))
);

CREATE TABLE IF NOT EXISTS mensajes_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL,
    remitente TEXT NOT NULL CHECK (remitente IN ('ESTUDIANTE', 'CHATBOT')),
    contenido TEXT NOT NULL,
    intencion TEXT,
    fecha_envio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES sesiones_chat(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_grupos_periodo_semestre
ON grupos(periodo_id, semestre_id);

CREATE INDEX IF NOT EXISTS idx_materias_semestre
ON materias(semestre_id);

CREATE INDEX IF NOT EXISTS idx_asignaciones_grupo
ON asignaciones(grupo_id);

CREATE INDEX IF NOT EXISTS idx_horarios_asignacion
ON horarios(asignacion_id);

CREATE INDEX IF NOT EXISTS idx_opiniones_materia_profesor
ON opiniones(materia_id, profesor_id, estado);

CREATE INDEX IF NOT EXISTS idx_mensajes_sesion_fecha
ON mensajes_chat(sesion_id, fecha_envio);
