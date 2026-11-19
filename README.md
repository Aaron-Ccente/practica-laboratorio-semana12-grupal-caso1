# Caso 1 — Gestión de Préstamos de Equipos de Laboratorio (UNCP)

Práctica grupal Semana 12 — Desarrollo de Aplicaciones Web, IS093A. **Solo Caso 1**.

## Instalación con Visual Studio Code / PowerShell

```powershell
cd Caso1_Prestamos_UNCP
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
$env:DEMO_PASSWORD = 'DemoLocal_12345!'
python manage.py crear_datos_demo
python manage.py createsuperuser
python manage.py runserver
```

Abre http://127.0.0.1:8000/ y http://127.0.0.1:8000/admin/ . En Linux/macOS activa el entorno con `source .venv/bin/activate` y define `export DEMO_PASSWORD='...'`.

**Usuarios de prueba:** `admin_lab`, `docente01`, `docente02`, `docente03`, `asistente01`. La contraseña indicada en `DEMO_PASSWORD` solo se aplica cuando el usuario se crea por primera vez. Para cambiarla usa `python manage.py changepassword nombre_usuario`. El superusuario debe crearse por separado. No compartas contraseñas reales ni publiques tu `.env`.

## Organización

- `config/`: settings, rutas y servidores WSGI/ASGI.
- `prestamos/models.py`: equipos, laboratorios, préstamos y auditoría.
- `prestamos/forms.py`: ModelForm y validaciones por campos y cruzadas.
- `prestamos/services.py`: préstamos y devoluciones transaccionales, validación de stock dentro de la transacción.
- `prestamos/middleware.py`: log de accesos denegados y avisos de préstamos vencidos.
- `prestamos/admin.py`: filtros, búsquedas, indicadores de estado y acciones masivas.
- `prestamos/management/commands/crear_datos_demo.py`: 10 equipos, 5 usuarios y 15 préstamos.
- `prestamos/tests.py`: pruebas de validación, permisos, sesiones, operaciones y configuración admin.
- `templates/` y `static/`: interfaz responsive.

## Roles y accesos

- **Administrador:** registrar/editar/eliminar equipos, consultar auditorías, informes y Django Admin (el usuario de demo `admin_lab` se crea como superusuario de prueba para tener acceso a Django Admin).
- **Docente:** solicitar y consultar únicamente su historial.
- **Asistente:** solicitar préstamos para docentes y registrar devoluciones.
- **Invitado:** consulta catálogo público.

El login institucional es **simulado**, no se conecta a servidores UNCP. No existe recuperación de contraseñas por correo. Se usa correo de consola (`EMAIL_BACKEND`) para los recordatorios del Django Admin; no se envían correos reales.

## Seguridad y validaciones

CSRF habilitado, cookies HttpOnly, sesiones de 30 minutos renovadas con actividad, hash de contraseñas de Django, protección de roles, restricciones de historial docente, auditoría de acciones sensibles. En desarrollo local, cookies `Secure` se desactivan para poder trabajar por HTTP; para producción define una clave secreta real, `DJANGO_DEBUG=0`, HTTPS, hosts correctos y `DJANGO_FORCE_HTTPS=1`.

Al crear préstamos se verifica la cantidad disponible dentro de una transacción. **SQLite no implementa bloqueo real de filas con `select_for_update()`**; para concurrencia intensiva de producción debe utilizarse PostgreSQL con bloqueos de fila, más pruebas de concurrencia. Esta versión sirve para práctica local.

## Pruebas

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test prestamos -v 2
```

## Capturas requeridas para la entrega

1. Solicitud válida: `Solicitar` con docente, equipo y fecha futura, luego confirmar en historial.
2. Solicitud inválida: fecha anterior o cantidad mayor que stock, captura del error.
3. Django Admin > Equipos: búsqueda, filtros y estado visual.
4. Django Admin > Equipos > acción “Marcar como en mantenimiento”; y Préstamos > “Enviar recordatorio de devolución”.
5. Terminal del servidor: accesos denegados (middleware) y la página Auditoría con acción.
6. Login + panel por rol y logout.
7. Usuario Docente intentando entrar a una vista de eliminación: muestra 403.
8. DevTools > Application > Cookies > `sessionid`, verificar `HttpOnly` y la expiración.

Guarda imágenes reales en `evidencias/caso1/`; no se adjuntan capturas ficticias.

## Entrega académica

Se debe proporcionar un repositorio público con README y requirements.txt, ramas `dev/integrante-1` y `dev/integrante-2`, Pull Requests, revisión de código y fusión. **Estos pasos deben hacerlos los integrantes; no se simulan.** Además, entregar un PDF con carátula, capturas por fase, descripción breve y reflexión individual de 2–3 párrafos.

## Limitaciones de verificación en el entorno de generación

Se realizó revisión estática y compilación de Python, pero **no fue posible ejecutar Django ni los tests aquí** porque la librería Django no está instalada y no hubo conexión al índice de paquetes. Ejecuta `pip install`, `migrate`, `check` y `test` en tu computadora, y reporta cualquier error obtenido para corregirlo.
