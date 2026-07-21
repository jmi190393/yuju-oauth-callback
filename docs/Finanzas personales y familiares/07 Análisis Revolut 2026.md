# 07 · Análisis Revolut (ene – jun 2026)

Fuentes: 6 estados de **tarjeta de crédito** Revolut (****9378 titular + ****0870 adicional) y CSV+PDF de la **cuenta débito** (ene–jun). Crédito conciliado al centavo los 6 meses (157 movimientos); débito con 256 filas.

## 🔑 El hallazgo que corrige el análisis de BBVA
La CLABE STP a la que BBVA enviaba los traspasos "mio" (clasificados antes como "inversión GBM") **es la cuenta Revolut**. El mapa real del dinero (ene–jun):

```
BBVA ──$1,029,368──▶ Revolut (cuenta Actual)
                        │
                        ├─▶ MXN Inversión (Rendimientos Diarios): rota ~$1.03M,
                        │     saldo al 30/jun: $237,763 · intereses ganados: ~$11,277 (≈$44/día)
                        ├─▶ eToro: $149,990 (mayo, 2 cargos con tarjeta)
                        ├─▶ GBM: $100,000 (SPEI)
                        ├─▶ BANORTE: $270,000 (26/feb — ¿destinatario? PREGUNTA ABIERTA)
                        ├─▶ regresos a BBVA: $207,000
                        └─▶ pago de la TDC Revolut: $49,591
```

**El "colchón invisible": $237,773 en Revolut Inversión** ganando ~8.9% anual con liquidez diaria. El diagnóstico de "no hay fondo de emergencia" se corrige: sí existe, pero está en Revolut y no se ve desde BBVA → razón #1 para el dashboard consolidado.

## Tarjeta de crédito Revolut (Premium)
- Corte: **fin de mes** · Fecha límite de pago: **día 20 del mes siguiente**.
- Hábito: los cargos no diferidos los paga casi de inmediato desde el saldo Revolut.
- ⚠️ **Pago de junio: $30,902.42 con fecha límite 20/jul/2026** — verificar que se haya cubierto.
- Uso por tarjeta (6 meses): titular ****9378 $61,081 · adicional ****0870 $65,254 (¿es la de Nurit?).

### MSI — sí hay, y muchos (corregido)
El usuario difiere sistemáticamente a **3 meses sin intereses (0%)** las compras grandes, sobre todo en viajes:
- **30 planes MSI en 2026** por un total diferido de **$97,350.59** (incluida la suscripción de Claude a 3 MSI de $1,159.32).
- Tandas: 27/mar (fin viaje China, 4 planes) · 4–15/abr (Corea/China + Claude, 20 planes) · 19/may (Miami: Apple $13,030, Vuori, Nordstrom, Nutrafol…, 6 planes).
- Al corte del 30/jun: **6 planes activos, $8,846.34 pendientes** — todos liquidan con su pago 3/3 en el ciclo de julio.
- ✅ Verificado: el "pago para no generar intereses" de junio ($30,902.42) es **exactamente** la suma de las mensualidades MSI exigibles de ese corte.
- Nota del periodo: los 3 MSI convierten el gasto de un viaje en 3 mensualidades — el módulo de pagos diferidos del sistema debe proyectar esto por mes y por tarjeta.

## Los viajes de 2026 (el uso real de Revolut)
| Viaje | Fechas | Gasto en Revolut |
|---|---|---|
| 🇦🇷 Argentina (Patagonia/Bariloche: Rapanui, Ovejitas) | ~5–8 ene | ~$3,240 débito (+ duty free $1,630) |
| 🇨🇳🇯🇵🇰🇷 Asia — China (Beijing, Shanghái, Xi'an, Tianjin), Japón (Tokio, Kobe), Corea (Seúl) | 18 mar – 7 abr | **$83,643** crédito |
| 🇺🇸🇧🇸 Miami/Aventura + Nassau (Bahamas) | 17–25 may | **$29,833** crédito |
| 🇬🇧 UK — pagó visa electrónica (ETA) el 8/jun | próximo viaje | $491 |

Gasto local MX con Revolut: mínimo (~$4.5k) — confirma la regla "Revolut = viajes".

## Suscripciones detectadas en Revolut
| Servicio | Monto | Cuándo | Nota |
|---|---|---|---|
| OpenAI (ChatGPT) | $110/mes | ene, feb, mar — **cesó tras marzo** | ¿cancelada o migró de tarjeta? |
| Anthropic Claude | $3,477.96 | 13/abr (tarjeta 0870) | ¿plan anual o mensual (Max)? |
| Nutrafol | $3,576.87 | 2/may | Suele ser suscripción — ¿recurrente? |
| Nintendo | $449 | 2/mar | ¿membresía o compra única? |

## Otros datos
- **Nurit Becker** transfiere ocasionalmente a la cuenta ($6,526 en 7 transferencias) — ¿aportes de la esposa al gasto común?
- RevPoints redondeo activo (microcargos de ~$8.6 con comisión $1.38 — costo marginal).
- Compra grande débito: Costco $8,653.65 (1/mar).
- La cuenta Actual se queda casi en $0 ($10.09 al 27/jun): todo duerme en Inversión. Buen hábito.

## Preguntas nuevas
Consolidadas en [[04 Preguntas abiertas]] — se harán todas juntas cuando el usuario confirme que no subirá más estados de cuenta.

## Implicaciones para el sistema
- **Importadores listos**: BBVA PDF ✅ · Revolut crédito PDF ✅ · Revolut débito CSV ✅.
- El sistema debe **consolidar saldos entre instituciones** para que el colchón real ($238k) sea visible — el problema nunca fue no tener reserva, sino no verla.
- Detección de transferencias internas (BBVA↔Revolut↔Inversión) para NO contarlas como gasto: sin esto, los números se inflan ~$2M.
- Los viajes se etiquetan solos por geografía del comercio (CHN/JPN/FL/BHS) — el módulo "viaje" es viable 100% automático.
