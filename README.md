# Finance Tracker (Django)

Aplicación web para gestión de movimientos financieros con autenticación, permisos por usuario, filtros avanzados y dashboard con gráficos.

## Funcionalidades incluidas

- **Modelos principales**
  - Usuario (Django Auth)
  - Tarjeta
  - Movimiento
  - TipoMovimiento
  - Categoria
- **Permisos**
  - Cada usuario puede crear/editar/eliminar **solo sus registros**.
  - Un usuario puede **ver** registros de otros usuarios en modo solo lectura.
- **Módulos funcionales**
  1. Lista de movimientos con filtros por fecha, monto, descripción, categoría, tipo, tarjeta y usuario.
  2. CRUD de tarjetas, categorías y tipos de movimiento.
  3. Dashboard con totales (ingresos, gastos, transferencias, balance), comparativa por usuario y gráfica mensual.
- **Admin de Django** configurado.
- **Templates responsive** con Bootstrap 5 + Chart.js.
- **Configuración dual de base de datos**
  - SQLite para desarrollo (por defecto).
  - PostgreSQL para producción usando `DATABASE_URL` (Supabase/Railway).

---

## Requisitos

- Python 3.11+
- pip

---

## Instalación local (desarrollo)

```bash
git clone <tu-repo>
cd finance_tracker
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Crear archivo `.env` basado en `.env.example` (opcional en desarrollo):

```bash
cp .env.example .env
```

Ejecutar migraciones y crear superusuario:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Levantar servidor:

```bash
python manage.py runserver
```

Abrir en navegador:
- App: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

> Nota: al crear un usuario, automáticamente se generan tipos de movimiento por defecto: **Ingreso, Gasto, Transferencia** (más categoría General).

---

## Estructura general

- `config/settings.py`: configuración principal y base de datos dual.
- `finances/models.py`: modelos de negocio.
- `finances/views.py`: módulos (dashboard, movimientos, CRUDs).
- `templates/`: vistas HTML responsive.
- `Procfile`, `runtime.txt`, `railway.json`: despliegue en Railway.

---

## Variables de entorno

Variables clave:

- `DEBUG` (True/False)
- `DJANGO_SECRET_KEY`
- `ALLOWED_HOSTS` (separados por coma)
- `CSRF_TRUSTED_ORIGINS` (URLs separadas por coma)
- `TIME_ZONE` (ej. `America/Matamoros`)
- `DATABASE_URL` (solo producción, PostgreSQL)
- `DB_SSL_REQUIRE` (True/False)

Si `DATABASE_URL` no existe, Django usará SQLite (`db.sqlite3`).

---

## Migración a PostgreSQL en Supabase

1. En Supabase, crea un proyecto y obtén la cadena de conexión PostgreSQL.
2. Define `DATABASE_URL` con formato:

```env
DATABASE_URL=postgresql://postgres:<PASSWORD>@<HOST>:5432/postgres
DB_SSL_REQUIRE=True
```

3. Ejecuta migraciones sobre PostgreSQL:

```bash
python manage.py migrate
```

4. (Opcional) Crear superusuario:

```bash
python manage.py createsuperuser
```

---

## Despliegue en Railway

### Archivos incluidos
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `railway.json`

### Pasos

1. Crear proyecto en Railway y conectar repo Git.
2. Configurar variables de entorno en Railway:
   - `DEBUG=False`
   - `DJANGO_SECRET_KEY=<valor-seguro>`
   - `ALLOWED_HOSTS=<tu-dominio-railway>`
   - `CSRF_TRUSTED_ORIGINS=https://<tu-dominio-railway>`
   - `DATABASE_URL=<connection-string-supabase>`
   - `DB_SSL_REQUIRE=True`
3. Deploy automático.
4. Railway ejecutará:
   - `python manage.py migrate`
   - `python manage.py collectstatic --noinput`
   - `gunicorn config.wsgi --log-file -`

---

## Comandos útiles

```bash
# Crear migraciones nuevas
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ejecutar tests
python manage.py test
```

---

## Seguridad y permisos implementados

- Autenticación con login/logout de Django.
- Edición/eliminación restringida a objetos donde `obj.usuario == request.user`.
- Listados visibles para todos los usuarios autenticados en modo lectura.

---

## Próximas mejoras sugeridas

- Tests unitarios por permisos y filtros.
- Exportación CSV/Excel de movimientos.
- Dashboard con más KPIs (ahorro mensual, tendencia por categoría).
