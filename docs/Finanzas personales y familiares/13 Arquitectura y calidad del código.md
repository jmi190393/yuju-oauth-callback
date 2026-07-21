# 13 · Arquitectura y calidad del código

Informe de la revisión de arquitectura (2026-07-21) aplicada al MVP durante su construcción, siguiendo los principios solicitados: simplicidad, DRY/KISS, escalabilidad y cero dependencias innecesarias.

## 1. Resumen ejecutivo
- **Stack**: FastAPI + SQLAlchemy + SQLite (un solo proceso, un solo archivo de BD) y una PWA en JavaScript puro **sin frameworks ni build step**. 5 dependencias totales.
- **Los importadores son el activo más valioso**: 4 parsers validados contra 18 estados reales, todos conciliando al centavo contra los totales oficiales del banco.
- Todo el sistema son ~2,600 líneas: cabe completo en la cabeza de una persona (o en el contexto de una IA) — ese era el objetivo de mantenibilidad.

## 2. Decisiones de arquitectura (y por qué)
| Decisión | Razón |
|---|---|
| SQLite por defecto, Postgres opcional vía `DATABASE_URL` | 2 usuarios, ~1k movimientos/año: SQLite sobra. Backup = copiar un archivo. Escalar = 1 variable de entorno |
| Sesión firmada HMAC en cookie + PBKDF2 (stdlib) | Evita dependencias de auth pesadas; suficiente y auditable para 2 usuarios |
| SPA vanilla JS (0 dependencias front) | Sin node_modules, sin build, sin actualizaciones rotas en 2 años. La PWA carga al instante |
| Categorización por reglas regex declarativas | Transparente y corregible; las reglas nacen del análisis real. Preparado para "aprender" de correcciones en fase 2 |
| Detección de banco por contenido, no por nombre de archivo | El usuario sube lo que sea; el sistema decide |
| Conciliación obligatoria en cada import | Herencia del análisis: si no cuadra al centavo con el banco, se avisa — nunca datos silenciosamente incompletos |
| Dedupe por hash (cuenta+fecha+desc+monto) | Subir dos veces el mismo estado es inofensivo (probado con el Platinum duplicado real) |

## 3. Problemas encontrados y corregidos durante la revisión
1. **Duplicación de planes MSI** (bug real): la semilla creaba planes que los importadores volvían a crear desde los estados → el flujo comprometido se inflaba ~$20k. *Fix*: la semilla ya no crea planes; los estados son la única fuente de verdad.
2. **Platinum sin sección de planes** (bug real): el estado bimestral no trae "Resumen de Planes"; el MSI automático de $163,405 solo existe como transacción "CARGO 01 DE 03" → el plan de $108,937 pendientes era invisible. *Fix*: el importador deriva el plan desde las transacciones marcadas cuando no hay resumen.
3. **Mes de primera mensualidad MSI**: Amex la carga al corte siguiente a la compra; Revolut en el mismo corte. Se modeló por banco (antes: off-by-one de un mes en el flujo).
4. Estructura `if/elif` defectuosa introducida en un fix (el `db.add` quedaba fuera de una rama) — detectada y corregida en la misma pasada.
5. Imports muertos (`datetime`, `timedelta`) eliminados; total anual de suscripciones ahora solo cuenta las **activas** (las "por confirmar" inflaban $43k/año).
6. ~44% de movimientos sin categoría tras el primer import → reglas nuevas para traspasos internos/pagos de tarjeta (los montos grandes que distorsionaban) + endpoint `POST /api/recategorize` para re-aplicar reglas mejoradas.

## 4. Verificación (regresión completa sobre datos reales)
- 18/18 estados importan y **concilian al centavo** (`ok` en los 18, `FAIL` en 0).
- Flujo MSI reproduce el análisis documentado: pendiente $136,602 · jul $63,315 · ago $56,758 · Bupa+KLM 1/3 $108,937 ✅ (cifras de [[08 Análisis Amex 2026]]).
- Patrimonio dashboard $3.53M ≈ tabla de [[09 Análisis Inversiones]] ✅.
- `py_compile` y `node --check` limpios; login de ambos usuarios probado; duplicados re-subidos = 0 filas nuevas.

## 5. Rendimiento y memoria
- Import de un estado: ~1–3 s (dominado por pdfplumber, inevitable). Todo lo demás: consultas indexadas (<10 ms con años de datos).
- Un solo proceso, ~60 MB RAM. Sirve para cualquier plan gratuito.

## 6. Riesgos conocidos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Los bancos cambian el layout del PDF | La conciliación lo detecta de inmediato (FAIL visible); solo hay que ajustar el parser afectado |
| SQLite sin respaldo | Documentado: copiar `finanzas.db` = backup total. Recomendado: respaldo automático semanal en fase 2 |
| Contraseña inicial compartida | El sistema exige cambio al primer ingreso |
| Planes MSI derivados de transacción usan (comercio+monto+meses) como identidad | Dos compras idénticas del mismo monto colisionarían — caso raro; se documenta |
| Hosting gratuito sin disco persistente (Render) | Documentado en README: usar PythonAnywhere/Fly con volumen o `DATABASE_URL` |

## 7. Recomendaciones futuras (fase 2+)
1. Aprendizaje de categorías: guardar cada corrección manual como regla nueva.
2. Respaldo automático de la BD (cron semanal → almacenamiento privado).
3. Bot WhatsApp (Meta Cloud API) reutilizando `POST /api/transactions` tal cual.
4. Alertas push (Web Push está preparado por ser PWA con service worker).
5. Tests automatizados de los parsers con PDFs sintéticos (hoy la validación es contra estados reales, que no pueden ir al repo).

## 8. Mapa del código
```
sistema/
  app/main.py         arranque, estáticos, SPA fallback           (~40 líneas)
  app/api.py          toda la API REST                            (~600)
  app/models.py       9 tablas SQLAlchemy                         (~160)
  app/auth.py         sesión HMAC + PBKDF2, sin dependencias      (~80)
  app/categorizer.py  reglas declarativas de categorización       (~80)
  app/seed.py         datos reales iniciales                      (~150)
  app/importers/      bbva · revolut · amex · detección           (~450)
  static/             PWA completa (HTML+CSS+JS, 0 dependencias)  (~900)
```
