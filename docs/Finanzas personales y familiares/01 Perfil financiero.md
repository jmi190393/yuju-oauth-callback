# 01 · Perfil financiero (cuestionario completo)

Respuestas del cuestionario inicial — 2026-07-19.

## Contexto general
- **País/moneda**: México, MXN. Cuenta compartida con esposa en USD, casi sin uso.
- **Situación**: empleado de empresa familiar, **$200,000 MXN/mes brutos** (menos impuestos). Por abrir una empresa nueva como inversionista; aún no retira dinero de ahí.
- **Familia**: casado; **primer hijo nace el 11 de noviembre de 2026**. Casa propia.
- **Dolor principal**: no sabe al 100% dónde gasta; quiere control y saber cuánto sobra para invertir/ahorrar.
- **Éxito en 6 meses**: entender claramente su situación financiera.

## Ingresos
- Sueldo mensual **fijo** de $200k menos impuestos, depositado en **BBVA (Bancomer)** — todo el dinero entra ahí.
- Rendimientos de inversión: **GBM, eToro, Cetes Directo** + retorno Wortev Capital ($160/mes, 36 mensualidades va 29/36).
- Régimen fiscal: **RESICO** (persona física).

## Datos fiscales (CSF del 04/dic/2025 — para el módulo de facturación)
| Campo | Valor |
|---|---|
| RFC | **MIVJ9303192A9** |
| Nombre (como en CSF, para CFDI 4.0) | JAIME MITRANI VULFOVICH |
| Régimen | **626 — Régimen Simplificado de Confianza (RESICO)** desde 19/sep/2023 |
| Código postal fiscal | **52786** (Huixquilucan, Edo. de México) |
| Actividad económica | Servicios de consultoría en computación (100%) |
| idCIF | 15090592832 |
| Obligaciones | ISR provisional mensual y IVA definitivo mensual (**vencen día 17**) · Declaración anual (abril) |

> [!note] El PDF completo de la CSF (con domicilio y CURP) NO se guarda en el repo — solo estos campos, que son los que pide un portal de facturación. Los pagos al SAT vistos en BBVA cuadran con la obligación mensual del día 17.

## Cuentas y tarjetas
| Institución | Tipo | Notas |
|---|---|---|
| BBVA Bancomer | Débito / nómina | Aquí entra todo el ingreso |
| Amex Gold | Tarjeta de servicios | Aquí se cargan la mayoría de suscripciones |
| Amex Platinum | Crédito | Tiene MSI activos |
| Revolut | Crédito y débito | Tiene MSI activos |
| Banamex | Crédito | **Por cancelar** |
| Banco Safra (EUA) — cuenta USD compartida con Nurit | Ahorro (fondo de boda) | Uso muy esporádico |
| GBM / eToro / Cetes Directo | Inversión | Largo plazo, no piensa retirar |

- **Días de corte y pago**: no los sabe → se extraerán de los estados de cuenta.
- **Efectivo**: solo propinas y estacionamientos, pero también paga en efectivo parte del servicio doméstico y lavado de autos. **Sí quiere registrarlo.**
- Sin billeteras digitales ni cripto.

## Deudas
- **Ninguna deuda** (ni hipoteca, ni auto, ni préstamos).
- Única excepción: **compras a MSI** en Revolut y Amex Platinum (compras grandes se difieren). Requiere seguimiento de pagos diferidos.

## Gastos fijos mensuales (de memoria)
- Mantenimiento del domicilio
- Servicios: luz, agua, gas, internet, celular
- Seguros: gastos médicos mayores, coche, casa
- Persona de servicio doméstico (parte en efectivo)
- Lavado de coches (parte en efectivo)
- Gasolina + carga del **Tesla**
- Súper
- Doctor — seguimiento del embarazo

## Gastos anuales (concentrados en diciembre–enero)
Predial, tenencia, verificación, seguro de casa, seguros de coches, gastos médicos mayores. Varios se difieren a MSI. → El sistema debe **aprovisionar 1/12 mensual**.

## Suscripciones
- Recuerda: **Amazon Prime, Claude, Obsidian**. El resto se detectará en estados de cuenta.
- Mayoría en **pago anual** (por descuento), cargadas a **Amex**. Algunas vía **App Store**.
- Posibles suscripciones zombis: solo en App Store → revisar.

## Hábitos
- Hoy **no lleva ningún registro**; solo revisa cuánto pagar de tarjeta.
- Captura debe ser **lo más rápida y sencilla posible**.
- **Estrategia de pareja**: él y su esposa gastarán desde **una misma tarjeta** para centralizar la visibilidad.

## Presupuesto y metas
- No tiene método de presupuesto → pide propuesta (ver [[02 Decisiones de diseño]]).
- Quiere ahorrar **lo más posible** (sin cifra fija → maximizar el "sobrante invertible").
- **Metas**:
	1. Viajar
	2. Cuenta de ahorro para su hijo (estructura escalable: una por cada hijo futuro)
	3. Fondo de emergencia
	4. Conocer el costo real de los gastos de un bebé
- **Inversiones dentro del sistema**: control de ganancia/pérdida y gráfica de evolución del patrimonio "que no está a la vista". Horizonte largo plazo, sin retiros.

## Facturación (requisito importante)
- Necesita **recordatorios de pedir factura** en todos los gastos facturables.
- Idealmente: subir foto del ticket y que el sistema ayude a **autofacturar** (semi-automático; ver [[02 Decisiones de diseño]]).
- Hoy: solo factura lo que se acuerda, "para deducir impuestos".
- ⚠️ **Verificar con contador**: en RESICO persona física los gastos generalmente no son deducibles; confirmar si las facturas son para la empresa nueva u otra razón. El sistema etiquetará cada gasto por entidad fiscal.

## Preferencias de sistema
- Lo delegó todo con el criterio: **fácil, eficiente, escalable, optimizado, "for dummies"** — que cualquiera de la familia entienda las finanzas y pueda tomar acciones.
- **En la nube**: acceso desde cualquier dispositivo, en cualquier momento, para él y su esposa.
- **WhatsApp**: sí quiere — texto ("250 súper") o foto del ticket; el sistema deduce y, si no puede, pregunta.
- **Conexión bancaria**: sin costo económico. Puede descargar estados de cuenta de BBVA, Banamex, 2 Amex, Revolut, eToro, GBM, Cetes Directo el día que se le indique.
- Alertas, pantalla principal y estilo: delegados a recomendación (ver [[02 Decisiones de diseño]]).
