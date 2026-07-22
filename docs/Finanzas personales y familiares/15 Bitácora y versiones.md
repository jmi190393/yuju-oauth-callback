# 15 · Bitácora y versiones

Historial de construcción, despliegue y evolución del sistema. La versión instalada siempre se puede ver dentro de la app en **Más → Actualizar programa**.

## Estado actual
- **Versión**: 1.7
- **En vivo**: `https://jmi190393.pythonanywhere.com` (PythonAnywhere, plan gratuito)
- **Stack**: Flask + SQLAlchemy + SQLite · PWA en JavaScript puro (0 dependencias front) · 3 dependencias core + `anthropic` opcional (solo para el chat con IA del Asesor)
- **Datos**: 972 movimientos de 2026 cargados (25 estados de 10 instituciones), conciliados al centavo

## Historia del despliegue (lecciones)
1. **Primer intento con FastAPI**: la app se colgaba en PythonAnywhere (error 504/HARAKIRI). Causa: FastAPI es ASGI y PythonAnywhere corre uWSGI (solo WSGI); el puente `a2wsgi` se traba bajo uWSGI.
2. **Solución**: se reescribió la capa web en **Flask** (WSGI nativo, el framework de referencia de PythonAnywhere), reutilizando intacta toda la lógica (modelos, importadores, categorizador, siembra). Verificado bajo servidor WSGI real antes de reenviar.
3. **Página en blanco**: el service worker cacheaba respuestas rotas. Se reescribió a *network-first* (solo cachea estáticos exitosos).
4. **Carga de datos**: en vez de subir 18 PDFs a mano, se generó la base ya llena (`finanzas.db`) y se subió una sola vez.

## Bitácora de versiones
| Ver. | Qué trajo |
|---|---|
| 1.0 | MVP: cuentas, captura rápida, presupuesto "regla del sobrante", MSI, suscripciones, metas, dashboard de 5 preguntas, importadores (BBVA, Revolut ×2, Amex ×2), login de pareja. |
| 1.1 | **Catálogo asistido**: cola "Por catalogar" que agrupa por comercio y **aprende** de cada corrección (regla aprendida). Revolut crédito → Viajes por defecto. **Importación masiva** (varios archivos). Pestaña **Actualizar programa**. |
| 1.2 | Crear categorías al vuelo (**➕ Otra…**), chips en **orden alfabético**, **🧹 limpiar** categorías sin usar. Nuevas: Ropa, Regalos, Peluquería y salón, Uber y transporte (distingue Uber de Uber Eats). |
| 1.3 | **Reclasificar cuando quieras** (pantalla *Editar categorías* + botón *Cambiar*). **Referencia completa** (beneficiario/folio) en movimientos y en la cola, para identificar pagos ambiguos. |
| 1.4 | **Rediseño UX completo** (sistema de diseño, light/dark, texto justificado, micro-interacciones). **Agrupar misma empresa**: ignora el número que cambia ("UBER TRIP 4821" = "UBER TRIP 9930"). Limpieza de arquitecto (código muerto, `pyflakes` limpio). |
| 1.5 | **Asesor** (Más → Asesor). Consejos automáticos gratis: **detector de gastos hormiga** (mismo comercio, 4+ compras chicas, equivalente mensual/anual), costo anual de suscripciones, meses para el fondo de emergencia con el sobrante, mes pico de MSI, concentración de riesgo. **Chat con IA (Claude, `claude-opus-4-8`)** que solo recibe un resumen agregado (nunca cuentas ni movimientos) y degrada con gracia si no hay clave/red. Nueva dependencia opcional `anthropic`. |
| 1.6 | **Lo mejor de las mejores apps**, adaptado: **Puedo gastar hoy** (safe-to-spend por día, estilo PocketGuard) en Inicio; **Salud financiera 0–100** con 5 componentes; **Tendencia de gasto** de 6 meses (mini-gráfica SVG sin dependencias); **comparativo mes vs mes** por categoría (estilo Copilot); **detección de cargos recurrentes** no registrados como suscripción (estilo Rocket Money). Todo alimenta también el resumen que ve la IA. Sin tablas nuevas ni dependencias. |
| 1.7 | **Robustez + fórmulas verificadas contra el estándar de la industria** (ver [[05 Benchmark de apps]]). Nuevas: **Alertas de cobros inusuales** (un cargo ≥2.5× lo típico de ese comercio, estilo Fintonic) y **metas con fecha proyectada** (aporte requerido/mes + fecha estimada al ritmo del sobrante). Correcciones tras investigar la metodología real: recurrentes ahora exigen **monto estable** (no marca como suscripción un gasto variable); safe-to-spend divide entre **días restantes**; salud financiera **etiquetada honestamente** como índice propio. **Suite de pruebas automatizadas** (`tests/test_insights.py`, 13 casos, sin dependencias) y lecturas numéricas blindadas. |

## Cómo se prueba cada versión
Antes de entregar, un guion automatizado importa los 25 estados reales y valida:
- 25/25 conciliados al centavo contra los totales oficiales.
- Los 12 endpoints responden 200.
- Patrimonio $3,532,045 y MSI $136,602 constantes (cuadran con [[08 Análisis Amex 2026]] y [[09 Análisis Inversiones]]).
- Compilación de Python (`py_compile`) y JS (`node --check`) limpias; el diseño se verifica con capturas reales del navegador (Chromium).
- **Suite del Asesor** (`python3 tests/test_insights.py`, 13 casos, sin dependencias): casos borde (base vacía, ingreso $0 → sin divisiones por cero), agrupación de gastos hormiga, recurrentes solo con monto estable, alerta de cobro inusual, safe-to-spend, mes vs mes, proyección de metas, y el asesor con IA simulada (camino feliz) y sin llave (degradación). Corre igual en PythonAnywhere sin instalar nada.

## Respaldo y seguridad
- **Respaldo = copiar `finanzas.db`** (un solo archivo). Recomendado hacerlo antes de cada actualización y, idealmente, semanal.
- Contraseñas: PBKDF2; sesión firmada (HMAC) en cookie. Cambiar la contraseña inicial `finanzas2026` al primer ingreso.
- El repositorio debe permanecer **privado**. La base de datos con datos reales nunca se sube al repo (está en `.gitignore`).

## Próximos pasos (Fase 2)
Bot de WhatsApp (captura por texto o foto de ticket), OCR, módulo de facturación CFDI (RFC ya capturado en [[01 Perfil financiero]]), alertas push. Ver [[03 Blueprint del sistema]].
