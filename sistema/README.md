# Finanzas personales y familiares — Sistema (Fase 1 MVP)

PWA en español (MX) para Jaime y Nurit: cuentas, captura rápida, presupuesto con
"regla del sobrante", MSI, suscripciones, metas e importación de estados de cuenta.

## Correr local

```bash
cd sistema
pip install -r requirements.txt
python run.py            # http://localhost:8000
```

Al primer arranque se crea `finanzas.db` (SQLite) sembrada con las cuentas,
categorías, presupuestos, planes MSI, suscripciones y metas REALES del análisis 2026.

**Usuarios**: `jaime` y `nurit` · contraseña inicial `finanzas2026`
(el sistema pide cambiarla al entrar: Más → Seguridad).

## Importar estados de cuenta

Más → Importar. Formatos soportados (detección automática por contenido):

| Banco | Formato | Validado con |
|---|---|---|
| BBVA Libretón | PDF | 7 estados 2026, conciliados al centavo |
| Revolut crédito | PDF | 6 estados (incluye planes MSI "N/M") |
| Revolut débito | CSV (export de la app) | ene–jun 2026 |
| Amex Gold / Platinum | PDF | 10 estados (transacciones + planes MSI) |

Cada importación: detecta banco → parsea → **concilia contra los totales oficiales
del estado** → deduplica → categoriza automáticamente → sincroniza planes MSI y saldos.

## Desplegar en la nube (costo $0)

La app es un solo proceso (FastAPI + SQLite). Opciones:

1. **PythonAnywhere (free)** — persistente y con HTTPS, suficiente para 2 usuarios.
   Subir la carpeta, `pip install -r requirements.txt --user`, configurar la web app
   WSGI→ASGI o correr con uvicorn. La BD queda en el disco persistente.
2. **Fly.io / Railway / Render** — usar el `Dockerfile` incluido. Ojo: en Render free
   el disco NO es persistente; montar un volumen (Fly) o usar Postgres
   (`DATABASE_URL=postgres://...` ya está soportado).
3. **Mini-servidor en casa** — `python run.py` + Cloudflare Tunnel para HTTPS.

Variables de entorno: `PORT`, `DATABASE_URL` (opcional), `FINANZAS_SECRET`
(recomendado en producción), `FINANZAS_DB` (ruta del SQLite).

**Importante**: la BD contiene datos financieros personales — nunca exponerla, y
respaldar `finanzas.db` (es un solo archivo; copiarlo = backup completo).

## Arquitectura

```
app/
  main.py         FastAPI + estáticos + arranque (crea tablas y siembra)
  api.py          Toda la API REST (/api/...)
  models.py       SQLAlchemy: usuarios, cuentas, categorías, movimientos,
                  planes MSI, suscripciones, metas, aprovisionamientos, importaciones
  auth.py         Sesión firmada (HMAC) en cookie; PBKDF2 para contraseñas
  categorizer.py  Reglas de categorización (nacidas del análisis real)
  seed.py         Datos iniciales reales
  importers/      bbva.py · revolut.py · amex.py · __init__.py (detección)
static/           PWA: index.html, app.js (SPA sin dependencias), styles.css,
                  manifest, service worker
```

Fase 2 (siguiente): bot de WhatsApp, OCR de tickets, módulo de facturación CFDI,
alertas push. Ver `docs/Finanzas personales y familiares/03 Blueprint del sistema.md`.
