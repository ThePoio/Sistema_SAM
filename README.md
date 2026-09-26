# Plataforma Integral de Evaluaciones Organismos Publicos

Aplicacion academica fullstack construida con FastAPI, MongoDB Atlas y Vanilla JS. Incluye dos roles simulados: Administrador y Encargado de Area.

## Requisitos

- Python 3.11 o superior.
- Una cuenta de MongoDB Atlas y una base de datos accesible desde la IP de desarrollo.
- Git para clonar el repositorio.

## Instalacion

```powershell
git clone <URL_DEL_REPOSITORIO>
cd evaluaciones_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux/macOS, activa el entorno con `source .venv/bin/activate`.

## Variables de entorno

Copia `.env.example` como `.env` y completa la URI de Atlas:

```powershell
Copy-Item .env.example .env
```

- `MONGO_URI`: cadena de conexion de MongoDB Atlas.
- `DB_NAME`: nombre de la base de datos.
- `PORT`: puerto local del servidor.

## Ejecucion

Desde la carpeta `evaluaciones_app`:

```powershell
uvicorn app.main:app --reload --port 8000
```

Abre `http://127.0.0.1:8000`. La documentacion interactiva queda disponible en `/docs`.

Credenciales simuladas:

- Administrador: `admin` / `admin123`.
- Encargado: `encargado` / `encargado123`.

## Endpoints

- `POST /api/auth/login`: valida usuario, contrasena y rol.
- `POST /api/evaluations`: crea una evaluacion para un encargado; requiere rol admin.
- `GET /api/evaluations`: lista todas las evaluaciones para admin o las asignadas al encargado.
- `PUT /api/evaluations/{id}/progress`: actualiza avance y evidencia; requiere rol encargado.
- `POST /api/evaluations/{id}/analyze`: analiza la evidencia registrada.

## Prueba de concurrencia con `asyncio.to_thread`

El endpoint de analisis obtiene la evidencia desde MongoDB y ejecuta la funcion bloqueante `cpu_heavy_task` con:

```python
analysis = await asyncio.to_thread(cpu_heavy_task, evidence)
```

La funcion simula un procesamiento pesado con `time.sleep(3)` y calcula una huella SHA-256. `asyncio.to_thread()` la mueve a un hilo secundario para que el event loop de FastAPI pueda continuar atendiendo otras solicitudes mientras el analisis termina. Puede comprobarse desde la interfaz presionando **Analizar evidencia con IA** y, en otra pestaña o cliente HTTP, enviando simultaneamente un `GET /api/evaluations`; la segunda solicitud no debe esperar los tres segundos del procesamiento.
