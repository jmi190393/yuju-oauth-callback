# 08 · Análisis Amex Gold + Platinum (ene – jul 2026)

Fuentes: 6 estados de **Gold** (…3008, cortes 08/feb–08/jul) + 4 de **Platinum** (…1000, cortes 25/feb–25/jun; el de mayo-junio es bimestral). **582 transacciones y 51 filas de planes, todo conciliado contra los totales oficiales** (1 centavo de tolerancia por redondeo de Amex en un mes).

## Mecánica de las tarjetas (para el sistema)
| | Gold (…3008) | Platinum (…1000) |
|---|---|---|
| Corte | día **8** | día **25** |
| Fecha límite de pago | día **23** | día **17** del mes sig. |
| Tipo | Cargo (se paga completa) + Planea tu Pago | Crédito, límite $500,000 |
| MSI | Planes manuales (3–15 meses) | **Automático**: ≥$6,000 o moneda extranjera → 3 MSI |

## El gasto real (Gold es LA tarjeta de la casa)
Total de cargos ene–jul: **$796,714** (~$132,786/mes, incluye mensualidades de planes y seguros).

### Los rubros grandes
| Rubro | Total | Detalle |
|---|---|---|
| 🏥 **Seguros Bupa (gastos médicos)** | **$277,351** | ✅ Resuelto (21/jul): son **2 pólizas (Jaime y Nurit)** y el total anual se paga en **2 exhibiciones semestrales** (ene y may/jun) → aprovisionar ≈ $23,100/mes solo de Bupa |
| 🚗 Seguros Qualitas (2 autos) | $62,356 | oct $14,472 (6 MSI) + dic $47,884 (6 MSI) — ambos ya liquidados |
| 🛒 Online: Amazon+ML+MercadoPago | ~$59,300 | compras frecuentes, varias a MSI |
| 🍔 **Uber Eats** | $28,746 | **55 pedidos** (~$4,791/mes) — categoría invisible hasta hoy |
| 💊 Farmacias (San Pablo sobre todo) | $25,593 | $1,314 promedio, 24 visitas |
| 🛣 **Casetas (PASE)** | $14,145 | **148 cargos** — ~$2,357/mes en autopistas |
| ✈️ Viajes | $27,734 | KLM $12,112 (8 cargos may) + Aeroméxico $9,411 + Royal Caribbean $6,211 |
| 👶 **Bebé (identificable)** | ~$35,680+ | NIPT prueba prenatal $15,900 · Dr. Charua $8,000 (4 consultas) · Hospital Ángeles $6,403 · monitor Nanit $5,377 |
| 🛋 Hogar | ~$17,400 | IKEA $9,744 · Home Depot · Soluciones en Agua/H2OSYS $18,523 (¿sistema de agua?) |
| ❓ "TIENDA COM MEX E COMMER" | $37,506 | 25 cargos — no identificado, PREGUNTA |

### Recurrentes fijos detectados en Amex
- **AT&T $675/mes** · **Telmex $499/mes** · **Apple.com/Bill ~$146/mes en promedio (23 microcargos: $49–$399 — varias suscripciones Apple)** · OPD Huixquilucan (agua) ~$1,222 · Soluciones en Agua MAIM $517/mes · Dr. Charua $2,000/consulta.
- **No aparecen** Netflix/Spotify/Disney/Prime en ninguna tarjeta hasta ahora → ¿van con Apple, con la esposa, o anuales aún no visibles? PREGUNTA.

## Portafolio MSI Amex — 16 planes, $287,197 diferidos desde oct 2025
Historial completo en `amex_planes.csv`. Lo VIVO al último corte:

| Tarjeta | Planes activos | Saldo pendiente | Mensualidad |
|---|---|---|---|
| Gold (corte 08/jul) | 5 (iShop 9/15 y 9/12, Ópticas Lux 3/6, ML 3/12 ×2) | **$17,414** | $3,920/mes |
| Platinum (corte 25/jun) | 1 (MSI automático de Bupa+KLM: $163,405 → 1/3 pagado) | **$108,937** | **$54,468/mes** (jul y ago) |
| Revolut (corte 30/jun) | 6 (Miami) | $8,846 | liquidan en jul |
| **TOTAL comprometido** | | **≈ $135,197** | **julio ≈ $67,200 en MSI** |

📌 **Julio y agosto son meses pesados**: solo de mensualidades MSI hay ~$60k+/mes, encima del gasto corriente. El módulo de "flujo comprometido" del sistema habría avisado esto con semanas de anticipación.

## El calendario de seguros (la "cuesta" real)
- **oct–dic**: Qualitas auto 1 ($14.5k) · Zurich ($6.9k) · Qualitas auto 2 ($47.9k)
- **ene**: Bupa $139,763
- **may/jun**: Bupa otra vez $137,588 (⚠️ confirmar por qué)
- Total seguros 12 meses ≈ **$346,600** (~$28,900/mes a aprovisionar). Es LA cifra dominante de sus gastos fijos anuales.

## Preguntas nuevas (acumuladas en [[04 Preguntas abiertas]])
Bupa ×2 · "TIENDA COM MEX" · dónde están Netflix/Prime/Obsidian · qué es H2OSYS/Soluciones en Agua · desglose de suscripciones Apple.

## Implicaciones para el sistema
- Importador Amex listo (Gold y Platinum, transacciones + planes MSI con progreso N de M).
- Ya se puede construir el **presupuesto basado en datos reales**: la información de las 4 tarjetas + BBVA cubre ~95% del gasto familiar.
- El RFC de cada comercio viene en el estado → **el módulo de facturación puede pre-llenar el RFC emisor automáticamente**.
