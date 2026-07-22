"""Bot de WhatsApp (Meta Cloud API) — Fase 2.

Captura de gastos por texto ("150 uber", "super 423.50 bebe"), consulta rápida
("como voy") y deshacer ("borrar"). Solo responde a números autorizados y cada
mensaje se procesa una sola vez. Sin dependencias nuevas (urllib de la stdlib).

Variables de entorno (en el archivo WSGI, junto a las demás):
  WHATSAPP_VERIFY_TOKEN  cadena que tú eliges; se pega igual en Meta (webhook)
  WHATSAPP_APP_SECRET    App secret de Meta (firma cada webhook; obligatorio)
  WHATSAPP_TOKEN         token de acceso de Meta (para responder)
  WHATSAPP_PHONE_ID      id del número emisor de Meta
  WHATSAPP_USERS         "5215511111111:jaime,5215522222222:nurit"

Si faltan las variables, el webhook responde 403 y el resto de la app no se
entera: es un módulo opcional igual que la IA del Asesor.
"""
import hashlib
import hmac
import json
import os
import re
import unicodedata
import urllib.request
from datetime import date

from flask import Blueprint, g, request
from sqlalchemy import func

from .models import Transaction, User

wa = Blueprint("whatsapp", __name__, url_prefix="/api/whatsapp")

GRAPH_URL = "https://graph.facebook.com/v20.0"

# Monto al inicio o al final: "150 uber", "uber 150", "$1,250.50 super"
MONTO_RE = re.compile(r"^\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)$")

AYUDA = (
    "🤖 *Bot de finanzas*\n"
    "• Registra un gasto: _150 uber_ o _super 423.50_\n"
    "• Etiqueta bebé/viaje/factura: agrega _bebe_, _viaje_ o _factura_\n"
    "• ¿Cómo voy este mes?: escribe _como voy_\n"
    "• Borrar el último gasto: escribe _borrar_\n"
    "Todo se guarda en la app y se categoriza solo."
)

# Ids de mensajes ya procesados (Meta reintenta webhooks): LRU simple por proceso.
_SEEN: dict[str, None] = {}
_SEEN_MAX = 500


def _cfg(key):
    return os.environ.get(key, "")


def _users_map():
    """WHATSAPP_USERS='<tel>:<usuario>,...' → {tel: usuario}."""
    out = {}
    for pair in _cfg("WHATSAPP_USERS").split(","):
        if ":" in pair:
            tel, name = pair.split(":", 1)
            out[tel.strip()] = name.strip().lower()
    return out


def _norm(s):
    """minúsculas y sin acentos, para reconocer comandos escritos de cualquier forma."""
    s = unicodedata.normalize("NFD", s.lower().strip())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _valid_signature(req) -> bool:
    secret = _cfg("WHATSAPP_APP_SECRET")
    if not secret:
        return False
    sig = req.headers.get("X-Hub-Signature-256", "")
    expect = "sha256=" + hmac.new(secret.encode(), req.get_data(),
                                  hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expect)


def _send(to: str, text: str):
    """Responde por WhatsApp. Si la red está bloqueada (lista blanca del plan
    gratuito), el gasto ya quedó guardado: solo se pierde la confirmación."""
    token, phone_id = _cfg("WHATSAPP_TOKEN"), _cfg("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        return
    body = json.dumps({"messaging_product": "whatsapp", "to": to,
                       "type": "text", "text": {"body": text}}).encode()
    req = urllib.request.Request(
        f"{GRAPH_URL}/{phone_id}/messages", data=body,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except OSError:
        pass  # sin salida a internet: el registro ya está hecho


TAG_WORDS = {"bebe": "bebe", "viaje": "viaje",
             "factura": "facturable", "facturar": "facturable"}


def _parse_gasto(text: str):
    """'150 uber' / 'uber 150' / 'panales 899 bebe' → (monto, descripción, tags).

    Las etiquetas (bebe/viaje/factura) se separan primero; el monto debe quedar
    al inicio o al final de lo que resta."""
    tags, resto = [], []
    for w in text.strip().split():
        wn = _norm(w)
        if wn in TAG_WORDS:
            tags.append(TAG_WORDS[wn])
        else:
            resto.append(w)
    if len(resto) < 2:
        return None
    if MONTO_RE.match(resto[0]):
        monto, desc_words = resto[0], resto[1:]
    elif MONTO_RE.match(resto[-1]):
        monto, desc_words = resto[-1], resto[:-1]
    else:
        return None
    valor = float(monto.lstrip("$").replace(",", ""))
    if valor <= 0:
        return None
    return valor, " ".join(desc_words), ",".join(dict.fromkeys(tags))


def _registrar(valor, desc, tags, user):
    """Crea el gasto reutilizando la categorización de la app (reglas + aprendidas)."""
    from .api import _learned_rules, _resolve_category
    from .models import Account, Category
    cash = g.db.query(Account).filter(Account.kind == "efectivo").first() \
        or g.db.query(Account).first()
    cat_by_name = {c.name: c.id for c in g.db.query(Category)}
    cid, auto_tags = _resolve_category(desc, "", cat_by_name, _learned_rules())
    t = Transaction(account_id=cash.id, date=date.today(), description=desc,
                    amount=valor, direction="cargo", category_id=cid,
                    tags=tags or auto_tags, source="whatsapp",
                    created_by=user.id if user else None)
    g.db.add(t)
    g.db.commit()
    cat = g.db.get(Category, cid) if cid else None
    return t, cat


def _como_voy():
    from .api import _budget, _safe_to_spend
    month = date.today().strftime("%Y-%m")
    b = _budget(month)
    sts = _safe_to_spend(b, month)
    return (f"📊 *{month}*\n"
            f"Gastado: ${b['gasto_real']:,.2f}\n"
            f"Sobrante proyectado: ${b['sobrante_real_proyectado']:,.2f}\n"
            f"Puedo gastar hoy: ${sts['por_dia']:,.2f}/día "
            f"({sts['dias_restantes']} días restantes)")


def _borrar_ultimo(user):
    q = g.db.query(Transaction).filter(Transaction.source == "whatsapp")
    if user:
        q = q.filter(Transaction.created_by == user.id)
    t = q.order_by(Transaction.id.desc()).first()
    if not t:
        return "No hay gastos de WhatsApp que borrar."
    g.db.delete(t)
    g.db.commit()
    return f"🗑️ Borré: {t.description} ${t.amount:,.2f}"


def _responder(texto: str, user) -> str:
    """Un mensaje entrante → una respuesta. Toda la 'inteligencia' del bot."""
    n = _norm(texto)
    if n in ("hola", "ayuda", "help", "?", "menu"):
        return AYUDA
    if "como voy" in n or n == "resumen":
        return _como_voy()
    if n in ("borrar", "deshacer", "borra el ultimo"):
        return _borrar_ultimo(user)
    gasto = _parse_gasto(texto)
    if not gasto:
        return ("No entendí 🤔. Escribe monto y concepto, ej. _150 uber_.\n"
                "O escribe _ayuda_ para ver qué puedo hacer.")
    valor, desc, tags = gasto
    t, cat = _registrar(valor, desc, tags, user)
    etiqueta = f" · 🏷 {t.tags}" if t.tags else ""
    if cat:
        return f"✅ Registré ${valor:,.2f} en {cat.emoji} *{cat.name}* ({desc}){etiqueta}"
    return (f"✅ Registré ${valor:,.2f} ({desc}){etiqueta}\n"
            f"Sin categoría aún: la eliges en la app en *Por catalogar* y la aprendo.")


@wa.get("/webhook")
def verify():
    """Verificación inicial del webhook (la hace Meta una sola vez)."""
    args = request.args
    if (args.get("hub.mode") == "subscribe"
            and _cfg("WHATSAPP_VERIFY_TOKEN")
            and args.get("hub.verify_token") == _cfg("WHATSAPP_VERIFY_TOKEN")):
        return args.get("hub.challenge", ""), 200
    return "forbidden", 403


@wa.post("/webhook")
def receive():
    """Mensajes entrantes. Siempre 200 rápido (Meta reintenta si no)."""
    if not _valid_signature(request):
        return "forbidden", 403
    payload = request.get_json(silent=True) or {}
    permitidos = _users_map()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                mid, tel = msg.get("id", ""), msg.get("from", "")
                if not mid or mid in _SEEN:
                    continue
                _SEEN[mid] = None
                if len(_SEEN) > _SEEN_MAX:
                    _SEEN.pop(next(iter(_SEEN)))
                if tel not in permitidos:
                    continue  # números desconocidos: silencio total
                if msg.get("type") != "text":
                    _send(tel, "Por ahora solo entiendo texto 📝 (la foto de "
                               "tickets viene en la siguiente fase).")
                    continue
                user = g.db.query(User).filter(
                    func.lower(User.name) == permitidos[tel]).first()
                _send(tel, _responder(msg["text"].get("body", ""), user))
    return "ok", 200
