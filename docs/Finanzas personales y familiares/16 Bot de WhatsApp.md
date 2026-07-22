# 16 · Bot de WhatsApp (Fase 2 · v2.0)

Captura de gastos **mandando un mensaje de WhatsApp**: `150 uber` y listo — se guarda en la app, se categoriza solo (con las mismas reglas aprendidas) y te responde la confirmación. Funciona para Jaime y Nurit, cada quien desde su teléfono.

## Qué sabe hacer (v2.0)
| Escribes | Pasa |
|---|---|
| `150 uber` o `uber 150` | Registra el gasto y lo categoriza solo |
| `panales 899 bebe` | Registra + etiqueta 👶 bebé (también `viaje`, `factura`) |
| `como voy` | Responde: gastado, sobrante proyectado y "puedo gastar hoy" |
| `borrar` | Borra tu último gasto capturado por WhatsApp |
| `ayuda` | El menú de arriba |

**Seguridad**: solo responde a los 2 números autorizados (a desconocidos: silencio total), cada webhook viene **firmado por Meta** y se valida (HMAC), y cada mensaje se procesa una sola vez aunque Meta lo reintente. La foto de tickets (OCR) queda para la siguiente fase.

## Configurarlo (una sola vez, ~20 min)
El bot usa la **API oficial de Meta (WhatsApp Cloud API)** — para uso personal (ustedes escribiéndole al bot) el costo es **$0**; Meta solo cobra mensajes de plantilla iniciados por la empresa, que no usamos.

### A. Crear la app en Meta (lo haces tú)
1. Entra a **developers.facebook.com** con tu cuenta de Facebook → *My Apps* → **Create App** → tipo **Business**.
2. En la app: *Add product* → **WhatsApp** → *Set up*. Meta te da:
   - un **número de prueba** (desde ahí responde el bot),
   - el **Phone number ID** (cópialo),
   - un **token temporal** (dura 24 h; abajo hacemos el permanente).
3. En *API Setup* → **To** → agrega tu celular y el de Nurit como destinatarios (llega un código por WhatsApp). El número de prueba admite hasta 5.
4. **App secret**: *App settings → Basic → App Secret* (cópialo).

### B. Conectar el webhook
5. En *WhatsApp → Configuration → Webhook*: 
   - **Callback URL**: `https://jmi190393.pythonanywhere.com/api/whatsapp/webhook`
   - **Verify token**: inventa una frase (ej. `finanzas-webhook-2026`) — la misma que pondrás abajo.
   - *Verify and save* → luego en **Webhook fields** suscríbete a **messages**.

### C. Variables en PythonAnywhere
6. En el **archivo WSGI** (el mismo del despliegue, antes de `from wsgi import application`):
```python
import os
os.environ["WHATSAPP_VERIFY_TOKEN"] = "finanzas-webhook-2026"   # la frase del paso 5
os.environ["WHATSAPP_APP_SECRET"]  = "el-app-secret-del-paso-4"
os.environ["WHATSAPP_TOKEN"]       = "el-token-de-meta"
os.environ["WHATSAPP_PHONE_ID"]    = "el-phone-number-id"
os.environ["WHATSAPP_USERS"]       = "521XXXXXXXXXX:jaime,521YYYYYYYYYY:nurit"
```
   (Los teléfonos van como los muestra Meta: código de país + número, sin `+` ni espacios.)
7. **Web → Reload** y manda `hola` al número de prueba. Debe contestar el menú. 🎉

### D. Token permanente (para que no muera a las 24 h)
8. **business.facebook.com** → *Configuración del negocio → Usuarios del sistema* → crear usuario del sistema (rol admin) → **Generar token** seleccionando tu app con el permiso `whatsapp_business_messaging` → reemplaza `WHATSAPP_TOKEN` en el WSGI → Reload.

## Si algo no jala
- **La verificación del webhook falla** → el verify token del WSGI y el de Meta no son idénticos, o falta el Reload.
- **El gasto se guarda pero no responde** → plan gratuito de PythonAnywhere: la salida a `graph.facebook.com` puede estar bloqueada (misma historia que la IA). Los mensajes ENTRAN igual (Meta nos llama a nosotros); solo se pierde la confirmación. El plan Hacker (~$5 USD/mes) lo resuelve — y de paso enciende la IA del Asesor.
- **No responde nada** → ¿tu número está en `WHATSAPP_USERS` tal como lo muestra Meta? El bot ignora números desconocidos a propósito.

## Cómo está construido (técnico)
- `app/whatsapp.py` (~200 líneas), blueprint `/api/whatsapp/webhook`, **cero dependencias nuevas** (urllib de la stdlib).
- Reutiliza el categorizador + reglas aprendidas de la app (`_resolve_category`) y el presupuesto (`_budget`) para `como voy`.
- 9 pruebas automatizadas (`tests/test_whatsapp.py`): firma HMAC, autorización, dedupe de reintentos, parser, comandos.
- Si las variables no están configuradas, el webhook responde 403 y **el resto de la app ni se entera** (módulo opcional, igual que la IA).

## Qué sigue (Fase 2.1)
Foto del ticket → OCR → gasto (requiere descargar la imagen de Meta + OCR); recordatorios proactivos por WhatsApp (requiere plantillas); facturación CFDI. Ver [[03 Blueprint del sistema]].
