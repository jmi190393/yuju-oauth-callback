# 13 · Arquitectura y calidad del código

Informe de arquitectura y calidad del sistema (Fase 1 MVP). Actualizado 2026-07-22 (v1.8) tras sumar el Asesor (consejos automáticos + IA) y un segundo pase de optimización de arquitecto.

## 1. Resumen ejecutivo
- **Stack**: **Flask** (WSGI puro) + SQLAlchemy + SQLite, y una PWA en JavaScript puro **sin frameworks ni build step**. 3 dependencias en total.
- **Por qué Flask y no FastAPI**: PythonAnywhere (el hosting elegido, gratis) corre **uWSGI**, que solo habla WSGI. FastAPI es ASGI y requiere un puente (a2wsgi) que **se cuelga bajo uWSGI** (HARAKIRI/504 en cada request). Flask es WSGI nativo y el framework de referencia de PythonAnywhere → cero fricción. La lógica de negocio (modelos, auth, categorizador, importadores, siembra) es agnóstica y se reutilizó intacta al cambiar de framework.
- **Los importadores son el activo más valioso**: 4 parsers validados contra 18 estados reales (25 archivos), todos conciliando al centavo contra los totales oficiales del banco.
- Todo el sistema son ~2,400 líneas: cabe completo en la cabeza de una persona (o en el contexto de una IA).

## 2. Decisiones de arquitectura (y por qué)
| Decisión | Razón |
|---|---|
| Flask (WSGI nativo) | Compatible con uWSGI sin puentes; despliegue robusto en hosting gratuito |
| SQLite por defecto, Postgres opcional vía `DATABASE_URL` | 2 usuarios, ~1k movimientos/año: SQLite sobra. Backup = copiar un archivo |
| Sesión firmada HMAC en cookie + PBKDF2 (stdlib) | Sin dependencias de auth; auditable; suficiente para 2 usuarios |
| Sesión de BD por request (`before/teardown_request`) | Aísla cada petición; libera conexiones siempre |
| SPA vanilla JS (0 dependencias front) | Sin node_modules, sin build; carga al instante; sin roturas por updates |
| Categorización por reglas regex declarativas | Transparente y corregible; nace del análisis real; `POST /api/recategorize` re-aplica reglas mejoradas |
| Detección de banco por contenido, no por nombre de archivo | El usuario sube lo que sea; el sistema decide |
| Conciliación obligatoria en cada import | Si no cuadra al centavo con el banco, se avisa — nunca datos silenciosamente incompletos |
| Dedupe por hash (cuenta+fecha+desc+monto) | Subir dos veces el mismo estado es inofensivo (probado con el Platinum duplicado real) |
| Service worker network-first, solo cachea `r.ok` | El SW nunca sirve una versión rota/vacía (ver incidente abajo) |

## 3. Problemas encontrados y corregidos
### Del despliegue (bugs reales)
1. **Cuelgue total en PythonAnywhere (HARAKIRI/504)**: causa = FastAPI(ASGI) sobre uWSGI(WSGI) vía a2wsgi. Se descartó primero como problema de streaming de estáticos (arreglo parcial), y al persistir el HARAKIRI se identificó la causa real y se **reescribió la capa web en Flask**. Verificado bajo servidor WSGI real: sirve sin colgarse.
2. **Página en blanco pese al servidor sano**: el service worker cacheaba *cualquier* respuesta (sin verificar `r.ok`) y servía el cascarón roto en cada carga. Reescrito a **network-first, cachear solo estáticos exitosos, purgar cachés viejas** al subir versión.

### De la lógica (corregidos durante la construcción)
3. **Duplicación de planes MSI**: la semilla creaba planes que los importadores volvían a crear → el flujo comprometido se inflaba ~$20k. La semilla ya no crea planes; los estados son la única fuente de verdad.
4. **Platinum sin sección de planes**: el estado bimestral no trae "Resumen de Planes"; el MSI automático de $163,405 solo existe como transacción "CARGO 01 DE 03". El importador ahora **deriva el plan desde las transacciones** cuando no hay resumen.
5. **Mes de primera mensualidad MSI**: Amex la carga al corte siguiente a la compra; Revolut en el mismo corte. Modelado por banco.

### Del pase de optimización (2026-07-21)
6. **Código muerto eliminado**: `get_db()` (dependencia de FastAPI, ya sin uso) y un import forzado en `main.py`.
7. **N+1 en `/api/transactions`**: cada movimiento disparaba consultas extra por su cuenta/categoría. Añadido `joinedload` → 1 consulta en vez de ~200.
8. **DRY**: la conversión USD→MXN repetida en 5 lugares se centralizó en `to_mxn()`.

### Del segundo pase de optimización (2026-07-22 · v1.8)
9. **Un solo escaneo para todo el Asesor**: la pantalla del Asesor calculaba gastos hormiga, recurrentes, alertas, tendencia y "mes vs mes" cada uno con su propia consulta → **4 escaneos completos de movimientos + 8 agregaciones mensuales + ~6 lecturas de categorías**. Se refactorizó a **un único `_load_cargos()` + un índice de comercios (`_spend_index`) + una carga de categorías**, y todo lo demás se deriva en memoria. Fuente única de agrupación por comercio → menos código y menos por mantener. Comportamiento idéntico (garantizado por la suite de pruebas).
10. **Fórmulas verificadas contra el estándar de la industria** (ver [[05 Benchmark de apps]]): se corrigió la detección de recurrentes (exige **monto estable**, ya no marca gasto variable como suscripción) y se etiquetó la salud financiera honestamente como índice propio.
11. **Lecturas numéricas blindadas** (`_setting_float`) y guardas contra división por cero en todos los indicadores nuevos.

### Del tercer pase — auditoría integral de arquitecto (2026-07-22 · v1.9)
Auditoría de **todo** el proyecto (3 revisiones en paralelo: importadores, backend, frontend). Se aplicó solo lo que aporta valor real; lo riesgoso sin red de pruebas se dejó documentado como recomendación.

**Seguridad**
12. **Cookie de sesión con `Secure`**: antes viajaba sin la marca `Secure`; ahora se activa en HTTPS (`secure=request.is_secure`) y se mantiene transparente en `http://localhost` para desarrollo. Sigue `HttpOnly` + `SameSite=Lax`.
13. **Login de tiempo constante**: si el usuario no existe, ya no se saltaba el PBKDF2 (un usuario inexistente respondía más rápido → permitía enumerar cuentas). Ahora se verifica siempre un **hash señuelo** (`DUMMY_HASH`) → mismo tiempo de respuesta. Bootstrap de `SECRET` reescrito (lectura del archivo con `with`, sin fugas de descriptor; recomendado `FINANZAS_SECRET` con varios workers).

**Escalabilidad (la palanca principal)**
14. **Índices en `transactions.category_id` y `account_id`**: SQLite no indexa las llaves foráneas solas, y esas dos columnas se filtran/agrupan constantemente (uncategorized, `GROUP BY category_id` del presupuesto, join por cuenta). Añadidos como `index=True` **y** con `CREATE INDEX IF NOT EXISTS` al arranque (idempotente) → los índices llegan también a la `finanzas.db` **ya existente**, no solo a bases nuevas.

**DRY / mantenimiento**
15. **`_networth(tc)`**: el patrimonio consolidado estaba calculado igual en 3 lugares → un solo helper.
16. **`money()` compartido en importadores**: `float(s.replace(",", ""))` estaba repetido **16 veces** en los 3 parsers → un helper (`importers/_util.py`), punto único para locale a futuro.
17. **Frontend**: `renderMovs` reescrito al patrón "shell fija + recarga solo de `#mlist`" → **corrige un bug real** (el buscador perdía el foco en cada tecla) y una carrera de respuestas fuera de orden (guarda `reqId`). `show()` ahora **captura errores** de render (una vista que falla muestra un aviso con "Reintentar" en vez de dejar el spinner colgado para siempre). Helpers `loading()` y `debounce()` (quitan 8 y 2 repeticiones). Ternario redundante y 3 clases CSS muertas eliminados.

**Robustez de importadores**
18. **Amex ya no truena** ante una línea con forma de transacción pero cuyo "mes" no es un mes real (`_mes` lanzaba `KeyError` y abortaba todo el import): ahora se valida `tm.group(2) in MESES` y esas líneas se tratan como continuación.

**Skips conscientes** (riesgo > valor sin la regresión de PDFs reales, que no corre en este entorno): refactor de doble extracción de páginas en BBVA, unificación de mapas de meses entre módulos, limpieza de grupos de captura de regex no usados. Quedan como recomendaciones futuras.

## 4. Verificación (regresión completa sobre datos reales)
- **25/25 archivos** (18 estados 2026) importan y **concilian al centavo**; 0 fallos.
- Dashboard: patrimonio **$3,532,045** ≈ tabla de [[09 Análisis Inversiones]] ✅.
- MSI: pendiente **$136,602** · jul **$63,315** · ago **$56,758** = cifras de [[08 Análisis Amex 2026]] ✅.
- Suscripciones activas: **$19,318/año** (AT&T + Telmex + iCloud + Claude anual) ✅.
- `py_compile` de todo Python y `node --check` de sw.js: limpios. Login de ambos usuarios y dedupe (re-subida = 0 nuevos) probados.
- **Suite del Asesor** (`tests/test_insights.py`, 13 casos) + **suite de importadores** (`tests/test_importers.py`, 3 casos: `money()`, mapa de meses, detectores). Sin dependencias; **16/16 en verde** tras cada refactor → el comportamiento es idéntico. Corren en PythonAnywhere sin instalar nada.
- **Cookie de sesión**: verificado que en HTTPS trae `Secure`+`HttpOnly`+`SameSite`, y en HTTP local no trae `Secure` (dev sigue funcionando). Índices `ix_transactions_category_id/account_id` verificados presentes tras el arranque.
- **Frontend**: verificado con Chromium que el buscador de Movimientos **conserva el foco** al escribir y filtra en vivo (5→3 filas), y que el clic en una fila abre la edición.

## 5. Rendimiento y memoria
- Import de un estado: ~1–3 s (dominado por pdfplumber; inevitable). El resto: consultas indexadas <10 ms con años de datos. El `joinedload` quitó el N+1 de la lista de movimientos.
- Un solo proceso, ~50 MB RAM (Flask es más ligero que FastAPI+uvicorn+a2wsgi). Sirve para cualquier plan gratuito.

## 6. Impacto de los pases de optimización
| Dimensión | Impacto |
|---|---|
| Rendimiento | Lista de movimientos O(1) consultas en vez de O(n); **Asesor de ~18 consultas de movimientos/categorías a 2** (1 escaneo + 1 carga de categorías, resto en memoria); menos overhead de framework |
| Memoria | Menor (3 deps core vs 6; sin event loop ASGI). El Asesor carga los cargos una vez por request y los libera al terminar |
| Mantenimiento | −código muerto, −repetición (`to_mxn`, `_spend_index` como fuente única de agrupación), routing Flask simple, **suite de pruebas** que fija el comportamiento |
| Escalabilidad | El Asesor ya no crece en nº de consultas al agregar indicadores (todos leen del mismo escaneo). Postgres a 1 variable de entorno cuando haga falta |

## 7. Riesgos conocidos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Los bancos cambian el layout del PDF | La conciliación lo detecta al instante (FAIL visible); se ajusta solo el parser afectado. Amex ya no aborta ante líneas ambiguas (v1.9) |
| `SECRET` de sesión efímero con varios workers | En PythonAnywhere gratuito = 1 worker (no aplica). Recomendado fijar `FINANZAS_SECRET` si algún día se escala a varios procesos |
| SQLite sin respaldo | Copiar `finanzas.db` = backup total; recomendado respaldo semanal |
| Planes MSI derivados usan (comercio+monto+meses) como identidad | Dos compras idénticas del mismo monto colisionarían — caso raro, documentado |
| Hosting gratuito duerme cada 3 meses | PythonAnywhere manda correo con botón "Run until 3 months from today" |

## 8. Recomendaciones futuras (Fase 2+)
1. Aprendizaje de categorías: guardar cada corrección manual como regla nueva.
2. Respaldo automático semanal de la BD a almacenamiento privado.
3. Bot WhatsApp (Meta Cloud API) reutilizando `POST /api/transactions` tal cual.
4. Alertas push (Web Push está listo por ser PWA con service worker).
5. Tests automatizados de los parsers con PDFs sintéticos (los reales no pueden ir al repo). *(El Asesor ya tiene suite propia; falta la de importadores.)*

## 9. Mapa del código
```
sistema/
  wsgi.py             expone la app Flask (WSGI nativo, sin puentes)   (~10 líneas)
  run.py              arranque local                                    (~10)
  app/main.py         Flask: estáticos, SPA, sesión de BD, siembra      (~45)
  app/api.py          blueprint /api (rutas REST + Asesor)              (~700)
  app/advisor.py      capa de IA (Claude): ai_available + ask_advisor   (~45)
  app/models.py       9 tablas SQLAlchemy                               (~160)
  app/auth.py         sesión HMAC + PBKDF2 + login_required             (~90)
  app/categorizer.py  reglas declarativas de categorización            (~80)
  app/seed.py         datos reales iniciales                            (~150)
  app/importers/      bbva · revolut · amex · _util(money) · detección (~460)
  static/             PWA completa (HTML+CSS+JS+SW, 0 dependencias)    (~1010)
  tests/              suite Asesor (13) + importadores (3), sin deps    (~290)
```
```
Dependencias core: flask · sqlalchemy · pdfplumber
Opcional (solo chat con IA del Asesor): anthropic
```
