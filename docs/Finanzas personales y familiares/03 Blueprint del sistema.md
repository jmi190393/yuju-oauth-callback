# 03 · Blueprint del sistema

Arquitectura funcional propuesta. Cada módulo nace de una necesidad real del [[01 Perfil financiero|perfil]].

## Módulos

### 1. Cuentas y saldos
Todas las cuentas en un lugar: BBVA (entrada de ingreso), Amex Gold, Amex Platinum, Revolut, efectivo, cuenta USD, Banamex (hasta cancelar). Saldo consolidado y por cuenta.

### 2. Transacciones
- Captura manual **ultra rápida** (monto + categoría en 2 toques) — clave para efectivo.
- Importación de **estados de cuenta** (PDF/CSV) con categorización automática.
- Conciliación: lo capturado a mano vs. lo importado, sin duplicados.
- Etiquetas especiales: `bebé 👶`, `facturable 🧾`, `entidad fiscal`.

### 3. Presupuesto — "Regla del sobrante"
Ver método en [[02 Decisiones de diseño]]. Topes por categoría basados en datos reales; el **sobrante invertible** como número central del mes.

### 4. Suscripciones
- Radar automático desde estados de cuenta (detecta cargos recurrentes).
- Registro de anuales (Amazon Prime, Claude, Obsidian…) con fecha de renovación y alerta 7 días antes.
- Vista "costo anual total de suscripciones" y detector de zombis (App Store).

### 5. MSI / Pagos diferidos
- Cada compra a MSI en Revolut o Amex Platinum genera su calendario de mensualidades.
- Vista de **flujo comprometido**: "de tus próximos 6 meses, ya debes $X/mes".
- Alerta cuando un plan termina (dinero que se libera).

### 6. Gastos anuales aprovisionados
Predial, tenencia, verificación, 3 seguros → apartado virtual de 1/12 al mes. En dic/ene el dinero ya existe.

### 7. Metas
- Viaje ✈️ · Cuenta del hijo 👶 (replicable por cada hijo futuro) · Fondo de emergencia 🛟
- Cada meta: monto objetivo, fecha, progreso, aportación sugerida desde el sobrante.
- **Informe "costo real de un bebé"**: acumulado automático de la etiqueta `bebé` desde el embarazo.

### 8. Inversiones / Patrimonio
- Registro de aportaciones y valor actual de GBM, eToro, Cetes Directo (actualización manual o por estado de cuenta).
- Gráfica de evolución del patrimonio + ganancia/pérdida. Solo lectura del "dinero que no se toca".

### 9. Facturación CFDI 🧾
- Cada gasto facturable con estado: `pendiente` / `facturado` / `no facturable`.
- Datos fiscales guardados; recordatorio antes de que venza el plazo del comercio.
- Semi-automático: de la foto del ticket se extraen folio/monto/fecha y se entrega liga directa al portal de autofacturación del comercio. Automatización total donde el portal lo permita.
- Etiqueta de entidad fiscal (RFC personal RESICO vs. empresa nueva).

### 10. Alertas y resúmenes
Catálogo completo en [[02 Decisiones de diseño]]. Resumen semanal + cierre mensual.

### 11. Bot de mensajería (fase 2)
Texto o foto de ticket → transacción registrada; diálogo de aclaración cuando falte información. Alimenta también facturación.

### 12. Multiusuario (pareja)
Dos cuentas de acceso, mismos datos. Diseño centrado en la **tarjeta única compartida**.

## Fases de construcción

### Fase 1 — MVP (el núcleo)
Cuentas · transacciones con captura rápida · categorías · presupuesto con sobrante invertible · suscripciones manuales · dashboard principal · importador de estados de cuenta (empezando por los bancos reales del usuario) · login pareja.

### Fase 2 — Automatización
Bot WhatsApp/Telegram · OCR de tickets · módulo de facturación completo · alertas push/mensaje · detector automático de suscripciones y MSI desde importaciones.

### Fase 3 — Profundidad
Metas avanzadas y aportaciones automáticas sugeridas · patrimonio/inversiones con gráficas históricas · informe del bebé · proyecciones ("si sigues así, en diciembre tendrás $X") · multi-hijo, multi-entidad.

## Principios técnicos
- **PWA web responsiva** en la nube, español mexicano, instalable en el celular.
- Costo de operación cercano a **$0** (sin agregadores bancarios de pago).
- Datos privados: solo dos usuarios, cifrado, sin compartir con terceros.
- Escalable: agregar cuentas, hijos, entidades fiscales o usuarios sin rediseñar.
