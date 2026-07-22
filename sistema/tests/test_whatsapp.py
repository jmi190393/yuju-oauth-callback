"""Pruebas del bot de WhatsApp: firma, autorización, dedupe, captura y comandos.
Sin red: el envío a Meta se captura con un mock. Sin dependencias externas:
    python3 tests/test_whatsapp.py
"""
import hashlib
import hmac
import json
import os
import sys
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))
os.environ["WHATSAPP_VERIFY_TOKEN"] = "verif-123"
os.environ["WHATSAPP_APP_SECRET"] = "secreto-app"
os.environ["WHATSAPP_USERS"] = "5215511111111:jaime,5215522222222:nurit"
# Sin WHATSAPP_TOKEN: _send no intenta red aunque el mock fallara.

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402
from app import whatsapp  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Transaction  # noqa: E402

ENVIADOS = []
whatsapp._send = lambda to, text: ENVIADOS.append((to, text))


def _firma(body: bytes) -> str:
    return "sha256=" + hmac.new(b"secreto-app", body, hashlib.sha256).hexdigest()


def _msg(texto, tel="5215511111111", mid=None, tipo="text"):
    m = {"id": mid or f"wamid.{texto}.{tel}", "from": tel, "type": tipo}
    if tipo == "text":
        m["text"] = {"body": texto}
    return {"entry": [{"changes": [{"value": {"messages": [m]}}]}]}


def _post(payload, firmar=True):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if firmar:
        headers["X-Hub-Signature-256"] = _firma(body)
    ENVIADOS.clear()
    return app.test_client().post("/api/whatsapp/webhook", data=body, headers=headers)


def test_verificacion_webhook():
    c = app.test_client()
    r = c.get("/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=verif-123&hub.challenge=reto77")
    assert r.status_code == 200 and r.get_data(as_text=True) == "reto77"
    assert c.get("/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=MALO"
                 ).status_code == 403


def test_firma_obligatoria():
    assert _post(_msg("150 uber"), firmar=False).status_code == 403
    assert _post(_msg("150 uber x", mid="wamid.f1")).status_code == 200


def test_parse_gasto():
    p = whatsapp._parse_gasto
    assert p("150 uber") == (150.0, "uber", "")
    assert p("uber 150") == (150.0, "uber", "")
    assert p("$1,250.50 super la comer") == (1250.5, "super la comer", "")
    assert p("panales 899 bebe") == (899.0, "panales", "bebe")
    assert p("300 lentes factura") == (300.0, "lentes", "facturable")
    assert p("hola") is None            # sin monto
    assert p("150") is None             # sin concepto
    assert p("0 nada") is None          # monto cero


def test_captura_y_categoriza():
    r = _post(_msg("150 uber trip", mid="wamid.c1"))
    assert r.status_code == 200 and ENVIADOS, "debió responder"
    to, texto = ENVIADOS[0]
    assert to == "5215511111111" and "Registré" in texto and "$150.00" in texto
    db = SessionLocal()
    t = db.query(Transaction).filter(Transaction.source == "whatsapp") \
        .order_by(Transaction.id.desc()).first()
    assert t and t.amount == 150.0 and t.direction == "cargo"
    assert t.category_id is not None, "UBER debe categorizarse solo"
    db.close()


def test_dedupe_mismo_mensaje():
    db = SessionLocal()
    antes = db.query(Transaction).count()
    _post(_msg("99 cafe", mid="wamid.dup"))
    _post(_msg("99 cafe", mid="wamid.dup"))  # reintento de Meta: mismo id
    despues = db.query(Transaction).count()
    db.close()
    assert despues == antes + 1, "el reintento no debe duplicar el gasto"


def test_numero_desconocido_silencio():
    r = _post(_msg("150 uber", tel="5219999999999", mid="wamid.x1"))
    assert r.status_code == 200 and not ENVIADOS, "desconocidos: ni registrar ni responder"


def test_como_voy_y_ayuda():
    _post(_msg("como voy", mid="wamid.cv"))
    assert ENVIADOS and "Sobrante proyectado" in ENVIADOS[0][1]
    _post(_msg("ayuda", mid="wamid.ay"))
    assert ENVIADOS and "Registra un gasto" in ENVIADOS[0][1]


def test_borrar_ultimo():
    _post(_msg("77 chicles", mid="wamid.b1"))
    _post(_msg("borrar", mid="wamid.b2"))
    assert ENVIADOS and "Borré" in ENVIADOS[0][1] and "chicles" in ENVIADOS[0][1]


def test_no_texto_aviso():
    _post(_msg("", tipo="image", mid="wamid.img"))
    assert ENVIADOS and "solo entiendo texto" in ENVIADOS[0][1]


def _run():
    tests = [(n, o) for n, o in sorted(globals().items())
             if n.startswith("test_") and callable(o)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} pruebas pasaron.")
    return fails


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
