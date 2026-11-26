# Chatbot Escolar — Fase 1: Base de datos

Este paquete contiene el primer módulo del proyecto. Utiliza SQLite, que viene incluido
con Python; no requiere contratar un servidor ni crear una cuenta externa.

## 1. Requisitos

- Python 3.10 o superior.
- Visual Studio Code (recomendado).
- No necesitas instalar SQLite por separado para ejecutar el inicializador.

## 2. Crear el entorno e instalar dependencias

Abre PowerShell en la carpeta `chatbot_escolar_fase1` y ejecuta:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

Si PowerShell bloquea la activación, puedes ejecutar directamente:

```powershell
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

## 3. Crear la base de datos

Desde la carpeta raíz del proyecto ejecuta:

```powershell
py backend/app/database/init_db.py
```

Se creará el archivo:

`backend/data/chatbot_escolar.db`

## 4. Tablas incluidas

- `programas`: carrera o programa académico.
- `semestres`: número de semestre.
- `periodos_escolares`: enero-junio o agosto-diciembre.
- `grupos`: grupos ofertados por semestre y periodo.
- `materias`: materias de cada programa y semestre.
- `profesores`: catálogo de docentes.
- `asignaciones`: relación entre grupo, materia y profesor.
- `horarios`: días, horas y aulas de cada asignación.
- `opiniones`: calificaciones y comentarios de estudiantes.
- `sesiones_chat`: sesiones de conversación.
- `mensajes_chat`: mensajes del estudiante y respuestas del chatbot.

## 5. Regla de semestres pares e impares

La regla se aplicará en el backend al consultar la oferta:

- Periodo `ENERO_JUNIO`: semestres pares.
- Periodo `AGOSTO_DICIEMBRE`: semestres impares.

La base conserva todos los semestres; el backend filtrará cuáles se muestran según el periodo activo.

## 6. Importante

La base está creada sin datos escolares reales. Primero debemos confirmar cuántos semestres,
carreras o programas maneja la institución y después cargaremos los datos correctos.

Las opiniones quedan inicialmente como `PENDIENTE`; el dashboard podrá permitir que un
administrador las revise antes de publicarlas.

No se incluye todavía autenticación de administradores ni conexión del chatbot. Eso se
desarrollará en las siguientes fases.
