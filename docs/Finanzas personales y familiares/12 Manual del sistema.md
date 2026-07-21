# 12 · Manual del sistema (Fase 1 MVP)

El sistema vive en la carpeta `sistema/` del repositorio. Es una **PWA** (se instala en el celular desde el navegador), en español, con login para Jaime y Nurit.

## Entrar
- Usuarios: `jaime` y `nurit` · contraseña inicial: `finanzas2026`
- ⚠️ Cambiarla al primer ingreso: **Más → Seguridad**.

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

### ☰ Más
- **MSI**: planes activos + flujo comprometido de los próximos 6 meses
- **Suscripciones**: costo anual total + estado (activa/por confirmar/cancelada)
- **Metas**: progreso y actualización de montos
- **Cuentas**: saldos por institución (tocar para actualizar inversiones)
- **Importar**: subir estados de cuenta

## Importar estados de cuenta (el corazón del sistema)
Cada mes, descargar y subir en **Más → Importar**:

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

## Qué sigue (Fase 2)
Bot de WhatsApp (texto o foto del ticket), OCR, módulo de facturación CFDI con recordatorios, alertas push. Ver [[03 Blueprint del sistema]].
