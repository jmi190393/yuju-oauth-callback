# 15 · Bitácora y versiones

Historial de construcción, despliegue y evolución del sistema. La versión instalada siempre se puede ver dentro de la app en **Más → Actualizar programa**.

## Estado actual
- **Versión**: 1.4
- **En vivo**: `https://jmi190393.pythonanywhere.com` (PythonAnywhere, plan gratuito)
- **Stack**: Flask + SQLAlchemy + SQLite · PWA en JavaScript puro (0 dependencias front) · 3 dependencias totales
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

## Cómo se prueba cada versión
Antes de entregar, un guion automatizado importa los 25 estados reales y valida:
- 25/25 conciliados al centavo contra los totales oficiales.
- Los 12 endpoints responden 200.
- Patrimonio $3,532,045 y MSI $136,602 constantes (cuadran con [[08 Análisis Amex 2026]] y [[09 Análisis Inversiones]]).
- Compilación de Python (`py_compile`) y JS (`node --check`) limpias; el diseño se verifica con capturas reales del navegador (Chromium).

## Respaldo y seguridad
- **Respaldo = copiar `finanzas.db`** (un solo archivo). Recomendado hacerlo antes de cada actualización y, idealmente, semanal.
- Contraseñas: PBKDF2; sesión firmada (HMAC) en cookie. Cambiar la contraseña inicial `finanzas2026` al primer ingreso.
- El repositorio debe permanecer **privado**. La base de datos con datos reales nunca se sube al repo (está en `.gitignore`).

## Próximos pasos (Fase 2)
Bot de WhatsApp (captura por texto o foto de ticket), OCR, módulo de facturación CFDI (RFC ya capturado en [[01 Perfil financiero]]), alertas push. Ver [[03 Blueprint del sistema]].
