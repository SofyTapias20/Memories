# Memories: Recomendador de Planes

Proyecto Flask simple con MySQL, Jinja2, Bootstrap 5, autenticacion, recuperacion de contrasena, recomendaciones, favoritos, historial, busqueda por tags y panel de administrador.

Esta version trabaja los costos en COP, permite subir imagenes a las actividades, usa una estrella para favoritos y permite que el administrador cree, edite y elimine actividades.

## Requisitos

- Python 3.10 o superior
- MySQL activo desde XAMPP, MySQL Workbench o servicio local
- Base de datos MySQL unicamente

## Instalacion

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Crear la base de datos

Opcion 1: ejecutar `database.sql` en MySQL Workbench o phpMyAdmin. Ese archivo crea la base de datos y las tablas principales del proyecto.

Opcion 2: dejar que la app la cree automaticamente al iniciar. Debe existir un usuario MySQL con permisos para crear bases de datos.

Variables recomendadas en Windows PowerShell:

```powershell
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD=""
$env:MYSQL_DATABASE="memories_db"
```

Si tu XAMPP tiene password para `root`, cambia `MYSQL_PASSWORD`.

## Ejecutar

```bash
python app.py
```

La aplicacion intenta crear tablas, admin inicial, actividades precargadas y columnas opcionales para imagenes automaticamente. Si ya ejecutaste `database.sql`, la aplicacion reutiliza esa base.

## Admin inicial

- Email: `admin@memories.com`
- Contrasena: `Admin123*`

La contrasena se guarda hasheada con Werkzeug.

## Estructura

```text
/templates
/static
app.py
models.py
routes.py
requirements.txt
database.sql
```

La logica Python esta dividida en solo tres archivos para que sea facil de leer:

- `app.py`: configuracion, conexion MySQL, creacion de tablas y datos iniciales.
- `models.py`: modelos, categorias, moods y actividades precargadas.
- `routes.py`: rutas agrupadas en tres Blueprints simples: auth, main y admin.

## Funciones principales agregadas

- El administrador puede editar actividades desde el panel Admin.
- Los costos se muestran como `COP $`.
- Los usuarios pueden subir una imagen desde el detalle de una actividad y tambien adjuntarla en una sugerencia.
- El administrador puede subir imagenes al crear o editar actividades.
- Los favoritos se activan y desactivan con un boton de estrella.
- Los archivos subidos quedan en `static/uploads`.

## Recuperacion de contrasena

El token se genera con `itsdangerous`. En modo desarrollo el enlace temporal se muestra en pantalla y tambien queda registrado en la consola Flask para facilitar pruebas sin configurar SMTP.

## Despliegue en Railway

Este proyecto queda preparado para seguir la guia de despliegue:

1. Crear un repositorio nuevo en GitHub y subir el proyecto.
2. Crear un proyecto en Railway desde ese repositorio.
3. Agregar un servicio **MySQL** dentro del mismo proyecto.
4. En las variables del servicio web, crear `DATABASE_URL` apuntando a la variable URL del servicio MySQL, por ejemplo:
   `DATABASE_URL=${{MySQL.MYSQL_URL}}`
5. Agregar `SECRET_KEY` con una clave segura.
6. Railway usará el `Procfile` y ejecutará `gunicorn app:app`.
7. Generar el dominio público desde **Settings > Networking > Generate Domain**.
8. Revisar los logs del deployment si aparece algún error.

La aplicación acepta `DATABASE_URL` en producción y, si la URL empieza por `mysql://`, la adapta automáticamente al controlador `mysql+pymysql://`.

No subas `.env` ni `env` a GitHub. El archivo `.env.example` solo sirve como plantilla para las variables locales.

