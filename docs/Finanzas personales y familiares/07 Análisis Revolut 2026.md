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
- **Sin planes MSI activos** en ene–jun (las secciones de compras a meses vienen vacías los 6 meses).
- Corte: **fin de mes** · Fecha límite de pago: **día 20 del mes siguiente**.
- Hábito: la paga casi de inmediato tras cada compra (a veces el mismo día) desde el saldo Revolut.
- ⚠️ **Pago de junio: $30,902.42 con fecha límite 20/jul/2026** — verificar que se haya cubierto.
- Uso por tarjeta (6 meses): titular ****9378 $61,081 · adicional ****0870 $65,254 (¿es la de Nurit?).

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
1. ¿A quién fueron los **$270,000 a Banorte el 26/feb**? (en dic también salieron $500k a Banorte "donativo").
2. ¿La tarjeta adicional ****0870 es de Nurit?
3. ¿Ya pagaste los **$30,902.42** de la TDC Revolut (vencía 20/jul)?
4. Claude $3,477.96: ¿anual o mensual? · Nutrafol: ¿sigue activa? · ¿OpenAI la cancelaste?
5. ¿Cuánto tienes hoy en eToro y GBM? (para el módulo de patrimonio; con corte a jun: les entraron $149,990 y $100,000 desde Revolut).

## Implicaciones para el sistema
- **Importadores listos**: BBVA PDF ✅ · Revolut crédito PDF ✅ · Revolut débito CSV ✅.
- El sistema debe **consolidar saldos entre instituciones** para que el colchón real ($238k) sea visible — el problema nunca fue no tener reserva, sino no verla.
- Detección de transferencias internas (BBVA↔Revolut↔Inversión) para NO contarlas como gasto: sin esto, los números se inflan ~$2M.
- Los viajes se etiquetan solos por geografía del comercio (CHN/JPN/FL/BHS) — el módulo "viaje" es viable 100% automático.
