# 02 · Decisiones de diseño y recomendaciones

Respuestas a los puntos que se delegaron a recomendación (preguntas 33–40 y método de presupuesto).

## Método de presupuesto — "La regla del sobrante" 💡
Adaptación simplificada de YNAB (base cero) para alguien que empieza de cero registro:

```
Ingreso del mes
  − Fijos (servicios, seguros, servicio doméstico, mantenimiento…)
  − Aprovisionamiento anual (1/12 de predial, tenencia, seguros, verificación)
  − MSI comprometidos del mes (Revolut + Amex Platinum)
  − Variables planeados (súper, restaurantes, gasolina/carga, bebé…)
  = SOBRANTE INVERTIBLE  →  se reparte entre metas e inversión
```

- El **sobrante invertible** es el número protagonista del sistema: responde "¿cuánto puedo invertir/ahorrar este mes?".
- Cada categoría variable tiene un tope mensual sugerido (calculado con los estados de cuenta reales, no inventado).
- Los gastos anuales de dic/ene se **aprovisionan** mensualmente para eliminar la "cuesta de enero".

## Conexión bancaria (pregunta 33) — Recomendación: estados de cuenta, costo $0
- Los agregadores (Belvo, etc.) **cuestan dinero** y no cubren bien Amex/eToro/Revolut. Descartados por ahora.
- Flujo elegido: **subir estados de cuenta** (PDF/CSV) una vez al mes. El sistema:
	1. Detecta el banco y parsea los movimientos automáticamente.
	2. Categoriza cada gasto (aprendiendo de correcciones).
	3. Detecta suscripciones, MSI, cargos duplicados o inusuales.
	4. Concilia contra lo capturado a mano (evita dobles registros).
- El sistema **avisará qué día descargar** cada estado (después de cada corte).
- Documentos a subir cada mes: BBVA, Amex Gold, Amex Platinum, Revolut, Banamex (hasta cancelar), y mensual/trimestral: GBM, eToro, Cetes Directo.

## Captura por WhatsApp (pregunta 32) — Sí, fase 2
- **Texto**: "250 súper", "1,200 gasolina" → se registra solo.
- **Foto del ticket**: el sistema extrae comercio, monto, fecha y folio; si no puede, **pregunta** ("¿qué comercio es y a qué corresponde?").
- El mismo ticket alimenta el módulo de **facturación**.
- Nota de costos: la API oficial de WhatsApp (Meta Cloud API) tiene nivel gratuito para conversaciones iniciadas por el usuario, pero requiere alta de número/negocio; **Telegram es 100% gratis y más simple** de operar. Decisión pendiente en [[04 Preguntas abiertas]].

## Alertas recomendadas (pregunta 34)
| Alerta | Cuándo |
|---|---|
| 💳 Pago de tarjeta próximo | 3 días antes de la fecha límite |
| ✂️ Corte de tarjeta | El día del corte ("desde hoy los gastos van al siguiente mes") |
| 📊 Presupuesto de categoría | Al 80% y al 100% del tope |
| 🔁 Renovación de suscripción | 7 días antes (crítico en las anuales de Amex) |
| 📆 MSI | Mensualidad que termina este mes / nuevo compromiso detectado |
| 🧾 Facturación | Tickets pendientes de facturar por vencer (fin de mes) |
| ⚠️ Cargo inusual | Monto atípico o comercio nuevo grande |
| 📥 Estado de cuenta | "Ya puedes descargar y subir el estado de X" |
| 🗓 Aprovisionamiento anual | Recordatorio dic/ene de predial, tenencia, seguros |
| 📈 Resumen | Semanal (domingo) y cierre mensual con sobrante invertible |

## Pantalla principal (pregunta 35)
De arriba hacia abajo, respondiendo las preguntas en orden de importancia:
1. **¿Cuánto tengo?** — Saldo disponible real (BBVA + efectivo − pagos comprometidos).
2. **¿Cómo voy este mes?** — Gastado vs. plan, con semáforo verde/amarillo/rojo y **sobrante invertible proyectado**.
3. **¿Qué viene?** — Próximos pagos: tarjetas, servicios, MSI, renovaciones.
4. **¿Cómo van mis metas?** — Barras de progreso: viaje, cuenta del bebé, fondo de emergencia.
5. **¿Cuánto valgo?** — Patrimonio total con mini-gráfica de inversiones (GBM + eToro + Cetes).

## Estilo y principios (preguntas 37–40)
- **Idioma**: español mexicano; formato `$1,234.56 MXN`, fechas dd/mmm.
- **Diseño**: minimalista y limpio (estilo Copilot/Monarch), tarjetas grandes, semáforos de color, cero jerga financiera. **"For dummies"**: cada pantalla responde UNA pregunta clara.
- **Dos niveles de lectura**: vista simple por defecto (para toda la familia) y detalle expandible (para análisis).
- Ver análisis completo de referencias en [[05 Benchmark de apps]].

## Plataforma y arquitectura (preguntas 31 y 36)
- **App web responsiva** (PWA): se ve y funciona como app en el celular, sin pasar por tiendas; instalable en la pantalla de inicio.
- **En la nube con login**: dos usuarios (él y esposa), mismos datos, cualquier dispositivo.
- Escalable por diseño: multi-hijo, multi-cuenta, multi-entidad fiscal.
