# Biblioteca: API REST con FastAPI y SQLModel

Servicio web para administrar una biblioteca: catálogo de libros y autores, registro de socios y
control de préstamos con devolución, stock y multas por atraso. Las reglas de negocio se validan
en el servidor y cada situación de error responde con su código HTTP correspondiente.

## Primeros pasos

**Requisito:** Python 3.11 o superior.

1. Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows (en Linux o Mac: source .venv/bin/activate)
   ```

2. Instalar las dependencias:

   ```bash
   pip install -r requirements-dev.txt    # entorno de desarrollo completo
   pip install -r requirements.txt        # solo lo necesario para ejecutar la API
   ```

3. Levantar el servidor:

   ```bash
   fastapi dev main.py
   ```

Con el servidor en marcha, la documentación interactiva está en <http://127.0.0.1:8000/docs>
y permite probar cada endpoint con ejemplos precargados. Al arrancar se crea automáticamente el
archivo SQLite `biblioteca.db` en el directorio desde el cual se lanzó el comando.

### Cargar datos de prueba

```bash
python -m scripts.seed
```

El script inserta 4 autores, 5 libros (uno sin stock y otro con dos autores), 4 socios (uno de
ellos inactivo) y 4 préstamos que cubren cuatro situaciones: uno reciente, uno vencido que no se
devolvió, uno devuelto en término y uno devuelto con atraso (y por lo tanto con multa). Si la base
ya contiene información, el script no agrega nada.

## Referencia de la API

### Autores

| Método y ruta | Qué hace |
|---|---|
| `POST /autores` | Crea un autor (`201`) |
| `GET /autores` | Lista los autores, con paginación |
| `GET /autores/{id}` | Devuelve un autor (`404` si no existe) |
| `PUT /autores/{id}` | Reemplaza todos sus datos |
| `PATCH /autores/{id}` | Modifica solo los campos enviados |
| `DELETE /autores/{id}` | Elimina al autor (`204`) |

### Libros

Usan los mismos métodos y rutas base que los autores (`/libros` y `/libros/{id}`). Además:

| Método y ruta | Qué hace |
|---|---|
| `GET /libros?disponibles=true` o `false` | Filtra por existencia de stock |
| `POST /libros/{id}/autores/{autor_id}` | Vincula un autor con el libro (`201`; `409` si ya estaba vinculado) |
| `DELETE /libros/{id}/autores/{autor_id}` | Desvincula al autor (`204`; `404` si no estaba vinculado) |

### Socios

Usan los mismos métodos y rutas base que los autores (`/socios` y `/socios/{id}`). Además:

| Método y ruta | Qué hace |
|---|---|
| `POST /socios/{id}/baja` | Baja lógica: el socio queda inactivo; repetirla no tiene efecto |
| `GET /socios/{id}/prestamos` | Lista los préstamos del socio; `?activos=true` o `false` filtra por estado |

### Préstamos

| Método y ruta | Qué hace |
|---|---|
| `POST /prestamos` | Registra un préstamo (`201`) |
| `GET /prestamos/{id}` | Devuelve un préstamo |
| `POST /prestamos/{id}/devolucion` | Registra la devolución y calcula la multa |

### Convenciones generales

- **Paginación:** todos los listados aceptan `?limit=20&offset=0`. El límite va de 1 a 100 y el
  orden siempre es por id.
- **PUT y PATCH:** PUT requiere todos los campos; PATCH aplica únicamente los que se envían y
  rechaza los valores `null`.
- **Relación libros-autores (N a N):** cada libro incluye la lista de sus `autores`. Un libro puede
  tener varios autores y un autor varios libros. Eliminar un libro o un autor borra sus vínculos,
  pero nunca al otro extremo; desvincular tampoco modifica los préstamos.
- **Disponibilidad:** `disponibles=true` devuelve los libros con stock mayor a 0, `false` los de
  stock 0 y, sin el parámetro, se devuelven todos.

### Validaciones de datos

- El `id` lo asigna la base de datos; el cliente no lo envía.
- El ISBN se almacena sin guiones ni espacios (10 o 13 dígitos) y no puede repetirse.
- El email del socio se guarda en minúsculas y tampoco puede repetirse.
- `stock` admite valores de 0 a 1.000.000 y `anio` no puede ser posterior al año actual.
- Los ids deben ser enteros positivos; si están fuera de rango la respuesta es `422`.
- Los libros y socios con préstamos registrados no se pueden eliminar (`409`). En el caso de los
  socios corresponde usar `POST /socios/{id}/baja`.

## Reglas de negocio

| N.º | Regla | Código |
|---|---|---|
| 1 | Un socio puede tener como máximo 3 préstamos activos | `409` |
| 2 | No se presta un libro sin stock; cada préstamo descuenta 1 unidad | `409` |
| 3 | Un socio inactivo no puede pedir préstamos (aunque sí puede devolver) | `403` |
| 4 | El plazo es de 14 días: `fecha_vencimiento = fecha_prestamo + 14 días` | |
| 5 | Al devolver se repone el stock; la multa es $100 por cada día de atraso (0 si llegó a tiempo) | |
| 6 | Un préstamo ya devuelto no puede devolverse otra vez | `409` |
| 7 | Cualquier recurso inexistente responde | `404` |
| 8 | ISBN o email repetido | `409` |

Al crear un préstamo, los controles se aplican en este orden: socio o libro inexistente (404),
socio inactivo (403), tope de préstamos alcanzado (409) y falta de stock (409).

## Configuración

Los valores por defecto se pueden cambiar con variables de entorno o con un archivo `.env`
(`.env.example` sirve de plantilla):

| Variable | Valor por defecto | Para qué sirve |
|---|---|---|
| `BIBLIOTECA_DATABASE_URL` | `sqlite:///biblioteca.db` | Cadena de conexión a la base |
| `BIBLIOTECA_PLAZO_PRESTAMO_DIAS` | `14` | Días de plazo de cada préstamo |
| `BIBLIOTECA_MULTA_POR_DIA` | `100` | Importe ($) de la multa diaria por atraso |
| `BIBLIOTECA_MAX_PRESTAMOS_ACTIVOS` | `3` | Máximo de préstamos activos por socio |

## Pruebas y calidad de código

```bash
pytest                 # ejecuta los tests
pytest --cov           # además mide la cobertura (el mínimo exigido es 80 %)
ruff check .           # análisis estático (lint)
ruff format --check .  # verificación de formato
pyright                # verificación de tipos
```

Los tests trabajan con SQLite en memoria y un reloj simulado: no modifican `biblioteca.db` ni
dependen de la fecha real. El archivo `tests/api/test_prestamos.py` se organiza por regla de
negocio, con un caso exitoso y uno de error para cada una; las reglas 7 y 8 se prueban además en
los tests de cada recurso.

El workflow `.github/workflows/ci.yml` ejecuta las cuatro verificaciones en GitHub, con Python
3.11, 3.12 y 3.14, en cada push.

## Organización del código

```
main.py              # crea la aplicación y registra los routers
config.py            # configuración (variables BIBLIOTECA_*)
database.py          # conexión a la base y sesiones
dependencies.py      # dependencias de FastAPI: sesión, servicios, paginación y "hoy"
exceptions.py        # errores de negocio
api/
  routers/           # endpoints HTTP
  schemas/           # JSON de entrada y de salida
  error_handlers.py  # traducción de errores de negocio a códigos HTTP
models/              # tablas
repositories/        # consultas a la base
services/            # reglas de negocio
scripts/             # datos de ejemplo
tests/
```

## Decisiones de diseño

- **Arquitectura en capas:** `router` → `service` (reglas) → `repository` (consultas) → base de
  datos. Los services lanzan errores de negocio (`NotFoundError` → 404, `ForbiddenError` → 403,
  `ConflictError` → 409) y un único manejador los transforma en respuestas HTTP.
- **Control de stock:** el descuento se ejecuta en una sola sentencia condicionada (`stock > 0`)
  dentro de la misma transacción que el préstamo, de modo que dos pedidos simultáneos no puedan
  llevarse la última copia. La devolución usa una condición análoga para no reponer stock dos veces.
- **Integridad en la base:** SQLite se configura con claves foráneas activadas y una restricción
  `stock >= 0`; ante cualquier violación se responde `409` y no un error interno.
- **Fecha de "hoy" inyectable:** permite probar vencimientos y multas sin depender del calendario.
- **Multa:** se calcula con fechas (días de calendario) y con valores configurables.

## Limitaciones conocidas

- **Sin autenticación:** cualquier cliente puede usar todos los endpoints; los roles de
  bibliotecario y socio quedaron fuera del alcance.
- **Tope de préstamos por socio:** se controla antes de insertar, por lo que dos pedidos
  simultáneos del mismo socio podrían superarlo. El stock, en cambio, sí está protegido.
- **Multa:** se calcula al registrar la devolución; un préstamo vencido que sigue sin devolverse
  todavía no muestra multa acumulada.
- **Base de datos:** SQLite está pensada para desarrollo y prácticas. Las tablas se crean al
  iniciar, pero no hay migraciones: para cambiar el esquema de una base existente haría falta una
  herramienta como Alembic, y en producción convendría un servidor como PostgreSQL.
