# 12 · Manual del sistema (Fase 1 MVP · v1.7)

El sistema vive en la carpeta `sistema/` del repositorio. Es una **PWA** (se instala en el celular desde el navegador), en español, con login para Jaime y Nurit. **Desplegado en la nube en PythonAnywhere**: `https://jmi190393.pythonanywhere.com`.

## Entrar
- Usuarios: `jaime` y `nurit` · contraseña inicial: `finanzas2026`
- ⚠️ Cambiarla al primer ingreso: **Más → Seguridad**.
- **Instalarla como app**: abrir la URL en el celular → Compartir → *Agregar a pantalla de inicio*.
- **Diseño**: se adapta solo a modo claro u oscuro según el celular. Texto justificado, números tabulares.

## Las 5 pantallas

### 🏠 Inicio — las 5 preguntas
1. **¿Cuánto tengo?** — líquido real (BBVA + Revolut Actual + efectivo)
2. **¿Cómo voy este mes?** — semáforo + **sobrante invertible proyectado**
3. **¿Qué viene?** — cortes y pagos de tarjetas, MSI del mes, renovaciones
4. **¿Cómo van mis metas?** — fondo de emergencia, bebé, viaje
5. **¿Cuánto valgo?** — patrimonio consolidado (USD al tipo de cambio configurado)

### ＋ Capturar (el botón azul)
Para el efectivo y gastos al vuelo: **monto + categoría = 2 toques**. Etiquetas rápidas: 👶 bebé · ✈️ viaje · 🧾 facturar.

### 📋 Movimientos
Todos los movimientos (manuales + importados), filtro por mes y búsqueda. Tocar uno permite corregir categoría, etiquetas y estado de factura.

### 📊 Plan (presupuesto)
La **regla del sobrante** en vivo: ingreso − fijos − aprovisionamiento − MSI del mes − variables = sobrante invertible. Cada categoría con barra y semáforo (verde ≤80%, amarillo ≤100%, rojo excedido).

### 📝 Por catalogar (el catálogo asistido)
Cuando importas, el sistema clasifica solo lo que reconoce. Lo que NO sabe queda en **Por catalogar** (aparece en Inicio con un contador y en Más). Ahí ves cada comercio agrupado, de mayor a menor monto, con su **referencia** (beneficiario/folio, para identificar pagos ambiguos como "PAGO CUENTA DE TERCERO"). Le tocas su categoría y **el sistema la recuerda**: la próxima vez que aparezca ese comercio lo clasifica solo. Detalles clave:
- **➕ Otra…**: crea una categoría nueva escribiendo el nombre (ej. Ropa). Queda disponible y se recuerda.
- **Cambiar**: si te equivocas, tras elegir puedes rectificar al momento.
- **Orden alfabético** de las categorías para encontrarlas rápido.
- **Misma empresa unificada**: "UBER TRIP 4821" y "UBER TRIP 9930" cuentan como un solo comercio (ignora el número que cambia) → no te pregunta dos veces.
- **🧹 Quitar categorías que no uso**: borra las categorías sin ningún movimiento (nunca borra gastos).

### ✏️ Editar categorías (reclasificar cuando quieras)
En **Más → Editar categorías**: busca cualquier comercio, ve su categoría actual y cámbiala. Se actualizan **todos** sus movimientos y el sistema reaprende.

### 🤖 Asesor (ahorro e IA)
En **Más → Asesor**. Dos partes complementarias:
- **Consejos automáticos** (gratis, siempre funcionan, sin internet). Reúne lo mejor de las mejores apps de finanzas:
  - **Salud financiera 0–100** (estilo Fintonic): un solo número con 5 componentes (ahorro, fondo de emergencia, deuda MSI, gasto vs ingreso, suscripciones) y su explicación.
  - **Gastos hormiga**: compras chicas y frecuentes del mismo comercio (p. ej. varios Uber Eats), con su equivalente mensual y anual.
  - **Tendencia de gasto**: mini-gráfica de tu gasto real de los últimos 6 meses.
  - **Este mes vs. el pasado** (estilo Copilot): qué categorías subieron o bajaron y cuánto.
  - **Cargos recurrentes detectados** (estilo Rocket Money): servicios que se repiten mes con mes **con monto estable** y que quizá no tienes registrados como suscripción (los de monto muy variable no se marcan: eso es gasto variable, no un plan).
  - **Cobros inusuales** (estilo Fintonic): un cargo mucho más grande de lo normal para ese comercio (≥2.5× lo típico) — para cachar errores, duplicados o cargos no reconocidos.
  - Además: costo anual de suscripciones, meses para el fondo de emergencia con tu sobrante, mes más pesado de MSI y concentración de riesgo.
- En **Metas** cada objetivo muestra su **proyección**: cuánto apartar al mes para llegar a su fecha, y la fecha estimada de cumplimiento al ritmo de tu sobrante.
- En **Inicio** verás también **¿Puedo gastar hoy?** (estilo PocketGuard): cuánto te queda libre por día el resto del mes, ya restados fijos, seguros y MSI.
- **Pregúntale al asesor (IA)**: un chat con Claude para optimizar, ahorrar y decidir metas. Trae preguntas sugeridas ("¿En qué 3 cosas puedo ahorrar sin sufrir?"). **Solo se le comparte un resumen agregado** (totales y categorías) — nunca números de cuenta ni movimientos individuales. Es una ayuda, no sustituye a un asesor profesional. Se activa poniendo una clave de Anthropic en el servidor (ver [[14 Despliegue en PythonAnywhere]] · Paso 7); si no está, el chat lo avisa y los consejos automáticos siguen disponibles.

### ☰ Más
- **Asesor**: consejos automáticos de ahorro + chat con IA
- **Por catalogar**: gastos que el sistema no supo clasificar (te pregunta y aprende)
- **Editar categorías**: reclasificar cualquier comercio cuando quieras
- **MSI**: planes activos + flujo comprometido de los próximos 6 meses
- **Suscripciones**: costo anual total + estado (activa/por confirmar/cancelada)
- **Metas**: progreso y actualización de montos
- **Cuentas**: saldos por institución (tocar para actualizar inversiones)
- **Importar**: subir estados de cuenta (**uno o varios a la vez**)
- **Seguridad**: cambiar contraseña
- **Actualizar programa**: versión instalada + comando exacto para actualizar sin borrar datos

## Importar estados de cuenta (el corazón del sistema)
Cada mes, descargar y subir en **Más → Importar** (se pueden **seleccionar varios archivos a la vez**):

| Cuándo (tras el corte) | Documento |
|---|---|
| día 14 | BBVA (PDF) |
| día 8 | Amex Gold (PDF) |
| día 25 | Amex Platinum (PDF) |
| fin de mes | Revolut crédito (PDF) + débito (CSV desde la app) |

El sistema **detecta el banco solo**, concilia contra los totales oficiales del estado (avisa si no cuadra), no duplica si subes dos veces el mismo, categoriza automáticamente, sincroniza los planes MSI y actualiza saldos.

> [!tip] Validado con datos reales
> Los 18 estados de cuenta de 2026 (BBVA ×7, Revolut ×7, Amex ×11 con un duplicado detectado) importan y concilian al centavo. El flujo MSI reproduce exactamente el análisis: julio $63,315, agosto $56,758, septiembre se libera.

## Datos ya cargados al estrenar
Cuentas con saldos reales, categorías con topes basados en el gasto real 2026, suscripciones detectadas, metas (fondo 3 meses $450k, bebé, viaje), aprovisionamiento de seguros ($346,600/año) y los datos fiscales para la fase de facturación.

## Actualizar el programa (sin perder datos)
Toda la información vive en **un solo archivo, `finanzas.db`**, separado del código. Para actualizar:
1. Subir el ZIP nuevo (Files → Upload).
2. Consola Bash: `unzip -o ~/finanzas-*.zip -d ~/sistema` (solo sobrescribe el programa; **no toca `finanzas.db`**).
3. Web → Reload.

Respaldo opcional antes de actualizar: `cp ~/sistema/finanzas.db ~/respaldo-$(date +%F).db`. Verificar que no se perdió nada: contar movimientos con `sqlite3`/`python3` (debe seguir en 972+). El mismo instructivo vive dentro de la app en **Más → Actualizar programa**.

## Recordatorios (calendario del celular)
Se entregaron archivos `.ics` con alarmas mensuales:
- **Subir estados**: día 9 (Amex Gold), 15 (BBVA), 26 (Amex Platinum), 1 (Revolut).
- **Pago de tarjeta (4 días antes)**: día 13 (Platinum), 16 (Revolut), 19 (Gold).

## 💬 Bot de WhatsApp (v2.0)
Manda `150 uber` por WhatsApp y el gasto queda registrado y categorizado; `como voy` te responde el resumen del mes; `borrar` deshace. Solo funciona para sus 2 números. La guía de conexión (cuenta de Meta, 20 min, una sola vez) está en [[16 Bot de WhatsApp]].

## Qué sigue (Fase 2.1)
Foto del ticket (OCR), módulo de facturación CFDI con recordatorios, alertas push. Ver [[03 Blueprint del sistema]] y la bitácora [[15 Bitácora y versiones]].
