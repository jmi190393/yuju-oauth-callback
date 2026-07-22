# 05 · Benchmark de apps — qué tomamos de cada una

Análisis de las mejores apps de finanzas del mercado y qué adoptamos de cada una para este sistema.

| App | Lo mejor que tiene | Lo que adoptamos |
|---|---|---|
| **YNAB** | Presupuesto base cero: cada peso tiene un destino antes de gastarse | La filosofía, simplificada como [[02 Decisiones de diseño\|"regla del sobrante"]] — sin la curva de aprendizaje que YNAB exige |
| **Monarch Money** | El mejor diseño para **parejas**: cuentas compartidas, vista unificada, metas conjuntas | Multiusuario de pareja, dashboard de patrimonio neto, metas con progreso visual |
| **Copilot Money** | Diseño hermoso y categorización automática que aprende de tus correcciones | Estética minimalista, semáforos, categorización que mejora con el uso |
| **Rocket Money** | Radar de suscripciones: detecta recurrentes y avisa antes de renovar | El módulo de suscripciones completo, incluido el detector de zombis |
| **Fintonic** | Alertas inteligentes en español y contexto bancario hispano | El sistema de alertas accionables (no notificaciones ruidosas) |
| **Mint** (†2024) | Gratuita y automática — murió por depender de agregadores costosos | La lección: no depender de agregadores de pago; importación propia = costo $0 y control total |
| **Splitwise** | Simplicidad extrema para gastos entre dos personas | La captura en 2 toques y el "cualquiera de los dos registra" |

## Lo que **evitamos** (quejas comunes en estas apps)
- Categorización que hay que corregir eternamente sin que aprenda.
- Pantallas saturadas de números que nadie entiende ("no for dummies").
- Suscripciones caras para funciones básicas (YNAB ~$110 USD/año).
- Dependencia de conexiones bancarias que fallan o no existen en México.
- Falta de soporte real para MSI y facturación CFDI — **ninguna app extranjera lo tiene**; aquí es módulo de primera clase.

## Ventaja de construir propio
MSI mexicanos + CFDI/facturación + RESICO + aprovisionamiento de predial/tenencia + pareja con tarjeta única + costo real de un bebé: **ninguna app del mercado cubre esta combinación**. Este sistema sí, porque se diseña sobre un perfil real.

## Verificación de fórmulas contra el estándar de la industria (v1.7)
Al implementar el **Asesor** (v1.5→1.7) se investigó la **metodología real y documentada** de cada app para no inventar fórmulas. Resumen de lo que se validó y corrigió:

| Función | Estándar de la industria (fuente) | Cómo quedó aquí |
|---|---|---|
| **Puedo gastar hoy** (PocketGuard "In My Pocket") | Ingreso − recurrentes − metas − ya gastado, dividido entre los **días que faltan** del periodo (no los días totales). | ✅ Se divide entre días restantes; se restan fijos, aprovisionamiento y MSI. |
| **Detección de recurrentes** (Rocket Money / Plaid) | **≥3 ocurrencias**, con **monto estable (~≤10-20% de variación)**; los de monto variable se tratan aparte. | ✅ Se exige ≥3 meses **y monto estable** (≤25% o CV<0.15). Corrigió un falso positivo: un restaurante con cargos de $700–$3,200 ya **no** se marca como suscripción. |
| **Tendencias / mes vs mes** (Copilot / Monarch) | **Excluir transferencias y pagos de tarjeta** del gasto (solo mueven dinero, no son gasto nuevo). | ✅ Las categorías `transferencia`/`inversión`/`ingreso` se excluyen de todo cálculo de gasto. |
| **Salud financiera 0–100** | El score oficial de la CFPB es una **encuesta** (no un promedio ponderado); los umbrales estándar son 50/30/20 (ahorro 20%), fondo 3–6 meses, regla 28/36 de deuda. | ✅ Es un **índice propio** basado en esos umbrales, **etiquetado honestamente** como guía (no como el puntaje oficial de un banco). |
| **Metas** (YNAB "true expenses") | Apartar mensualmente para llegar a una fecha; proyección por ritmo de ahorro. | ✅ Cada meta muestra **aporte requerido/mes** para su fecha y **fecha estimada** al ritmo del sobrante. |

**Errores comunes que evitamos** (señalados en la investigación): dividir entre días totales en vez de días restantes; contar pagos de tarjeta como gasto; marcar comercios de monto variable como suscripción; e inventar pesos y presentarlos como "el método de la CFPB". Todo esto está cubierto por la **suite de pruebas** (`sistema/tests/test_insights.py`, 13 casos).
