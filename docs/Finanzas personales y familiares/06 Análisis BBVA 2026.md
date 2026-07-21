# 06 · Análisis BBVA (dic 2025 – jul 2026)

Fuente: 7 estados de cuenta Libretón BBVA (periodos del 15 al 14). **152 movimientos, conciliados al centavo** contra los totales oficiales de cada estado. Fecha de corte: **día 14** de cada mes.

## El hallazgo central: BBVA es tu "centro de distribución", no donde gastas
El dinero entra, y de ahí se reparte a 4 destinos: **inversión (GBM), pago de Amex, casa y familia**. El gasto real del día a día casi no pasa por la tarjeta de débito — vive dentro de los estados de Amex (siguiente análisis pendiente).

## Ingresos confirmados
| Concepto | Monto | Frecuencia |
|---|---|---|
| Nómina principal (BNET …7526) | **$153,522.87** | Mensual (fin de mes) |
| Nómina complemento (BNET …5315) | **$41,633.32** | Mensual |
| **Total neto mensual** | **≈ $195,156** | Consistente los 7 meses |
| Mensualidad entrante (venta a 36 pagos, va 29/36) | $160 | Mensual — quedan ~7 pagos |

## A dónde se fue el dinero (7 periodos)
| Destino | Total | Promedio/mes |
|---|---|---|
| 📈 Inversión GBM (neto: envió $797k, regresó $217k) | **$580,000** | ~$82,900 |
| 💳 Pago Amex A (…3008) | $576,612 | ~$96,000/mes en 2026 |
| 👨‍👩‍👦 Familia (donativo $500k dic + préstamo mamá $40k) | $540,000 | — (extraordinario) |
| 🏠 Mantenimiento "Serena 506" | $142,269 | **$21,798.61** fijo |
| 💳 Pago Amex B (…1000) | $101,933 | $9,289.34 fijo (¿MSI?) + pico $73,886 en jun |
| 🔁 Traspasos a otra cuenta propia BBVA (…9080) | $53,200 | — |
| 🌎 Orden de pago al extranjero (28/ene) | $35,265 | — (¿fondeo Revolut/eToro?) |
| 🧠 Psicólogo (Pablo) | $24,000 | ~$3,900 |
| 🏠 Servicio recurrente (Enrique Cruz) | $16,240 | **$2,320** fijo |
| 🐕 Kenai — paseador (Iván) | $15,400 | ~$1,925 (pagos semanales de $400–750) |
| 📈 Cetes Directo (domiciliado NAFIN) | $14,000 | **$2,000** fijo día ~1 |
| 🛒 Súper/comercios con débito (Costco, Walmart, 7-Eleven) | $15,696 | ~$2,200 |
| 🏛 SAT | $11,082 | Irregular ($1.1k–$4.7k) |
| 💳 Pago tarjeta Banamex | $8,054 | Pequeños y variables |
| Otros (transferencias personales, efectivo, varios) | ~$33,700 | — |

## Recurrentes fijos detectados (para el presupuesto)
- Mantenimiento casa: **$21,798.61** (día ~5; fue $15,477 en ene y $17,798 en jul — verificar por qué varía)
- Servicio E. Cruz: **$2,320** (~cada mes, día variable)
- Cetes domiciliado: **$2,000** (día ~1)
- Amex B: **$9,289.34** mensual exacto feb–abr → huele a **plan de pagos fijos/MSI** (confirmar con estados Amex)
- Psicólogo: $1,500–3,000 por sesión, ~2 por mes
- Kenai: ~$400–750 semanal

## 🚨 Señales que el sistema habría alertado
1. **Colchón en ceros**: el saldo pasó de $995k (dic) a **$6,496 el 14/jul**. Todo se invierte o gasta — disciplina de inversión excelente, pero **no existe fondo de emergencia líquido**. Con bebé en camino, es la meta #1.
2. **2/3 del gasto es invisible desde BBVA**: los ~$96k/mes de Amex A son una caja negra hasta subir esos estados. *(Amex A …3008 y Amex B …1000 — confirmar cuál es Gold y cuál Platinum.)*
3. **FANFIX.IO $198.09** (20/ene, cargo en USD a la tarjeta de débito): cargo tipo suscripción — ¿lo reconoces?
4. El pico de **$73,886 en Amex B (jun)** merece explicación (¿seguro anual? ¿compra grande a MSI?).
5. Pagos al SAT irregulares — el sistema los proyectará para que no sorprendan.

## Preguntas nuevas para Jaime
1. ¿Qué es la cuenta BBVA propia (…9080) que recibió $35,200 + $18,000 ("plac")? ¿Cuenta de tu esposa, o apartado?
2. ¿La orden de pago al extranjero de $35,264.60 fue fondeo a Revolut/eToro?
3. Los pagos a la cuenta origen de tu nómina ($8,957 "a1077429" y $4,616.80): ¿devoluciones/pagos a la empresa familiar?
4. ¿$3,490 a José Luis Aparicio (may) y $2,895×2 (ene, a Jaime MV y Nurit Becker) — qué fueron?
5. ¿Reconoces FANFIX.IO?
6. ¿Quién te paga los $160/mes (pedido a 36 mensualidades)?

## Implicaciones para el sistema
- El **importador BBVA ya existe** (parser conciliado al centavo) — será el primer conector del MVP.
- Categorización automática por contraparte (CLABE/nombre) funciona muy bien en BBVA: ~90% de los movimientos se clasifican solos.
- Los estados de **Amex son la prioridad #1** de carga: ahí está el detalle del gasto real (súper, restaurantes, suscripciones, MSI).
- El dashboard debe separar **flujo de vida** (casa, salud, mascota) de **flujo patrimonial** (GBM, Cetes, familia) — mezclarlos distorsiona el "gasto mensual".
