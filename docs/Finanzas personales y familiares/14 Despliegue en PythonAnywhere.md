# 14 · Despliegue en PythonAnywhere (paso a paso)

> [!warning] Seguridad
> La contraseña de PythonAnywhere se compartió por chat el 21/jul → **cambiarla** en cuanto el sistema quede montado (Account → Password), y no reutilizarla en otros servicios.

Guía para publicar el sistema en la cuenta gratuita de PythonAnywhere. Tiempo estimado: **10 minutos**. Solo se hace una vez.

## Paso 1 — Subir el código
1. Entra a **pythonanywhere.com** e inicia sesión.
2. Ve a la pestaña **Files**.
3. Con el botón **Upload a file**, sube el archivo `finanzas-sistema.zip` (te lo pasé por el chat).

## Paso 2 — Instalar (una consola, 3 comandos)
1. Pestaña **Consoles** → **Bash**.
2. Copia y pega estas líneas (una por una, Enter después de cada una):
```bash
unzip -o finanzas-sistema.zip -d ~/sistema
cd ~/sistema && pip3 install --user -r requirements.txt
python3 -c "import wsgi; print('LISTO')"
```
3. Debe terminar imprimiendo `LISTO`.

## Paso 3 — Crear la web app
1. Pestaña **Web** → **Add a new web app** → Next.
2. Elige **Manual configuration** (NO "Flask" ni "FastAPI" si aparece).
3. Elige la versión de **Python más nueva** que ofrezca (3.10 o superior) → Next.

## Paso 4 — Conectar el código
1. En la misma pestaña Web, sección **Code**, haz clic en el enlace del **WSGI configuration file** (algo como `/var/www/jmi190393_pythonanywhere_com_wsgi.py`).
2. **Borra todo** el contenido del archivo y pega solo esto (cambia `TUUSUARIO` por tu nombre de usuario de PythonAnywhere, el que aparece arriba a la derecha):
```python
import sys
sys.path.insert(0, "/home/TUUSUARIO/sistema")
from wsgi import application
```
3. Botón **Save**.

## Paso 5 — Encender
1. Regresa a la pestaña **Web** y presiona el botón verde **Reload**.
2. Abre `https://TUUSUARIO.pythonanywhere.com` — debe aparecer la pantalla de login 💰.

## Paso 6 — Primer uso (tú y Nurit)
1. Entren con `jaime` / `nurit` y la contraseña inicial `finanzas2026`.
2. **Cada uno cambia su contraseña**: Más → Seguridad.
3. En el celular: abrir la URL en Safari/Chrome → **Compartir → Agregar a pantalla de inicio** → queda instalada como app.
4. Subir los estados de cuenta en Más → Importar.

## Si algo falla
- Pantalla de error → pestaña Web → **Error log** (las últimas líneas dicen la causa). Mándame ese texto y lo resuelvo.
- La cuenta gratuita "duerme" la app cada 3 meses: PythonAnywhere manda un correo con un botón **"Run until 3 months from today"** — solo hay que presionarlo cuando llegue.

## Mantenimiento
- **Respaldo**: el archivo `~/sistema/finanzas.db` ES toda la base de datos. Descargarlo de vez en cuando (Files → sistema → finanzas.db → download).
- **Actualizaciones del sistema**: cuando yo publique mejoras, te paso el ZIP nuevo; se repiten los pasos 1–2 y Reload (la base de datos no se toca).
