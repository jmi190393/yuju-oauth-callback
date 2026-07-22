"""Pruebas reales del Asesor: consejos automáticos, salud financiera, safe-to-spend,
recurrentes, cobros inusuales y proyección de metas.

Sin dependencias externas (no requiere pytest): se corre con
    python3 tests/test_insights.py
y termina con código != 0 si algo falla. También es compatible con pytest.

Cada prueba parte de una base limpia (solo la siembra por defecto) y agrega sus
propios movimientos, de modo que las cifras son deterministas y verificables.
"""
import os
import sys
import tempfile

# Base de datos temporal aislada ANTES de importar la app.
os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date  # noqa: E402

from app.main import app, SessionLocal  # noqa: E402
from app.models import Rule, Setting, Transaction  # noqa: E402
from app.api import _is_stable, _median, _project_goal  # noqa: E402


def _client():
    c = app.test_client()
    c.post("/api/login", json={"user": "jaime", "password": "finanzas2026"})
    return c


def _reset(ingreso="120000"):
    """Deja la base con la siembra por defecto + un ingreso conocido, sin
    movimientos ni reglas de escenarios anteriores."""
    db = SessionLocal()
    db.query(Transaction).delete()
    db.query(Rule).delete()
    db.merge(Setting(key="ingreso_mensual", value=ingreso))
    db.commit()
    db.close()


def _add(rows):
    """rows: (fecha, descripción, monto, categoría|None)."""
    db = SessionLocal()
    from app.models import Account, Category
    acc = db.query(Account).first()
    cats = {c.name: c.id for c in db.query(Category)}
    for d, desc, amt, cat in rows:
        db.add(Transaction(account_id=acc.id, date=date.fromisoformat(d), description=desc,
                           amount=amt, direction="cargo", category_id=cats.get(cat),
                           source="manual"))
    db.commit()
    db.close()


def _mkey_month(off):
    t = date.today()
    y, m = t.year, t.month - off
    while m <= 0:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


# ---------------- pruebas unitarias (funciones puras) ----------------

def test_median():
    assert _median([]) == 0.0
    assert _median([5]) == 5
    assert _median([1, 3]) == 2
    assert _median([1, 2, 3]) == 2
    assert _median([10, 1, 100, 2]) == 6  # (2+10)/2


def test_is_stable():
    assert _is_stable([219, 219, 219]) is True            # suscripción típica
    assert _is_stable([100, 110, 105]) is True            # variación mínima
    assert _is_stable([700, 800, 3200]) is False          # gasto variable, NO recurrente
    assert _is_stable([100]) is True                      # un solo dato: no descarta
    assert _is_stable([100, 260]) is False                # 2.6x, no estable


def test_project_goal():
    # Meta ya cumplida
    p = _project_goal(0, 5000, None)
    assert p["cumplida"] is True and p["meses_estimados"] is None
    # Con sobrante, sin fecha meta → estima meses y fecha
    p = _project_goal(30000, 10000, None)
    assert p["meses_estimados"] == 3.0 and p["fecha_estimada"] is not None
    assert p["aporte_requerido"] is None
    # Con fecha meta futura → aporte requerido mensual
    futuro = date(date.today().year + 1, date.today().month, 1)
    p = _project_goal(24000, 0, futuro)
    assert p["aporte_requerido"] is not None and p["aporte_requerido"] > 0
    # Sin sobrante y sin fecha → nada que estimar, pero no truena
    p = _project_goal(30000, 0, None)
    assert p["meses_estimados"] is None and p["aporte_requerido"] is None


# ---------------- pruebas de integración (endpoints) ----------------

def test_endpoints_ok_con_base_vacia():
    """Con cero movimientos, ningún endpoint debe reventar (división por cero, etc.)."""
    _reset(ingreso="0")  # incluso con ingreso 0
    c = _client()
    for ep in ["/version", "/dashboard", "/insights", "/budget", "/msi",
               "/subscriptions", "/goals"]:
        r = c.get("/api" + ep)
        assert r.status_code == 200, f"{ep} devolvió {r.status_code}"
    ins = c.get("/api/insights").get_json()
    assert 0 <= ins["health"]["score"] <= 100
    assert ins["safe_to_spend"]["dias_restantes"] >= 1


def test_gastos_hormiga_agrupa_y_filtra():
    _reset()
    m1, m2 = _mkey_month(1), _mkey_month(0)
    _add([
        (f"{m1}-03", "UBER EATS 11", 180, None), (f"{m1}-11", "UBER EATS 22", 210, None),
        (f"{m2}-02", "UBER EATS 44", 190, None), (f"{m2}-09", "UBER EATS 55", 205, None),
        (f"{m2}-15", "UBER EATS 66", 175, None), (f"{m2}-20", "UBER EATS 77", 160, None),
        (f"{m2}-10", "MUEBLERIA CARA", 25000, None),  # grande: NO es hormiga
    ])
    ins = _client().get("/api/insights").get_json()
    keys = [h["description"] for h in ins["gastos_hormiga"]]
    assert any("UBER EATS" in k for k in keys), "debió detectar Uber Eats como hormiga"
    assert not any("MUEBLERIA" in k for k in keys), "un cargo grande no es hormiga"
    # los 6 cargos (con distinto número final) cuentan como UN comercio
    uber = next(h for h in ins["gastos_hormiga"] if "UBER EATS" in h["description"])
    assert uber["count"] == 6


def test_recurrentes_exige_monto_estable():
    _reset()
    m0, m1, m2 = _mkey_month(2), _mkey_month(1), _mkey_month(0)
    _add([
        # Netflix: mismo monto 3 meses → recurrente
        (f"{m0}-05", "NETFLIX MX 1", 219, "Suscripciones"),
        (f"{m1}-05", "NETFLIX MX 2", 219, "Suscripciones"),
        (f"{m2}-05", "NETFLIX MX 3", 219, "Suscripciones"),
        # Restaurante: 3 meses pero monto MUY variable → NO recurrente
        (f"{m0}-10", "RESTAURANTE X", 700, "Restaurantes"),
        (f"{m1}-10", "RESTAURANTE X", 800, "Restaurantes"),
        (f"{m2}-10", "RESTAURANTE X", 3200, "Restaurantes"),
    ])
    # Netflix está en Suscripciones sembradas? No; lo detecta como recurrente no registrado
    ins = _client().get("/api/insights").get_json()
    descs = [r["description"] for r in ins["recurrentes"]]
    assert any("NETFLIX" in d for d in descs), "Netflix (monto estable) debe ser recurrente"
    assert not any("RESTAURANTE" in d for d in descs), \
        "Restaurante con monto variable NO debe marcarse recurrente"
    # el monto reportado es la mediana (219), no un promedio inflado
    net = next(r for r in ins["recurrentes"] if "NETFLIX" in r["description"])
    assert net["avg"] == 219


def test_alerta_cobro_inusual():
    _reset()
    m0, m1, m2 = _mkey_month(2), _mkey_month(1), _mkey_month(0)
    _add([
        ("%s-08" % m0, "FARMACIA Z", 300, None),
        ("%s-08" % m1, "FARMACIA Z", 350, None),
        ("%s-08" % m2, "FARMACIA Z", 2000, None),  # 6x lo típico, reciente → alerta
    ])
    ins = _client().get("/api/insights").get_json()
    al = ins["alertas"]
    assert al and any("FARMACIA" in a["description"] for a in al), "debió alertar el cargo grande"
    a = next(a for a in al if "FARMACIA" in a["description"])
    assert a["amount"] == 2000 and a["veces"] >= 2.5
    # además debe aparecer como primer tip accionable
    assert ins["tips"][0]["title"].startswith("Cobro fuera")


def test_safe_to_spend_no_negativo_dividido():
    _reset(ingreso="1000")  # ingreso chico → disponible puede ser negativo
    _add([(f"{_mkey_month(0)}-05", "GASTO GRANDE", 50000, "Restaurantes")])
    d = _client().get("/api/dashboard").get_json()
    sts = d["como_voy"]["puedo_gastar_hoy"]
    assert sts["dias_restantes"] >= 1  # nunca divide entre 0
    assert isinstance(sts["por_dia"], (int, float))


def test_mom_filtra_sin_cambio():
    _reset()
    m1, m2 = _mkey_month(1), _mkey_month(0)
    _add([
        (f"{m1}-10", "RESTAURANTE Y", 800, "Restaurantes"),
        (f"{m2}-10", "RESTAURANTE Y", 3200, "Restaurantes"),  # subió 2400
        (f"{m1}-11", "SUPER", 500, "Súper"),
        (f"{m2}-11", "SUPER", 500, "Súper"),  # sin cambio → no debe listarse
    ])
    ins = _client().get("/api/insights").get_json()
    movers = ins["mom"]["movers"]
    assert any(m["name"] == "Restaurantes" for m in movers)
    assert all(abs(m["diff"]) >= 1 for m in movers), "no debe incluir cambios de $0"


def test_meta_proyeccion_en_dashboard():
    _reset()
    d = _client().get("/api/dashboard").get_json()
    metas = d["metas"]
    assert metas, "debe haber metas sembradas"
    assert all("proyeccion" in m for m in metas), "cada meta trae su proyección"


def test_advisor_sin_llave_degrada():
    _reset()
    r = _client().post("/api/advisor", json={"question": "¿Dónde ahorro?"}).get_json()
    assert r["ok"] is False and r["reason"] == "sin_config"
    assert "IA" in r["answer"] or "clave" in r["answer"].lower()


def test_advisor_con_llave_mock():
    """Camino feliz de la IA, con el SDK simulado (no gasta API real)."""
    import types
    fake = types.ModuleType("anthropic")

    class _Blk:
        def __init__(s, t):
            s.type = "text"
            s.text = t

    class _Msg:
        content = [_Blk("• Recorta X.\n• No sustituyo a un asesor.")]

    def _create(**kw):
        assert kw["model"] == "claude-opus-4-8"
        assert "system" in kw and kw["messages"]
        return _Msg()

    client = types.SimpleNamespace(messages=types.SimpleNamespace(create=_create))
    fake.Anthropic = lambda *a, **k: client
    sys.modules["anthropic"] = fake
    os.environ["ANTHROPIC_API_KEY"] = "sk-test"
    try:
        _reset()
        r = _client().post("/api/advisor", json={"question": "¿Dónde ahorro?"}).get_json()
        assert r["ok"] is True and "Recorta" in r["answer"]
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        sys.modules.pop("anthropic", None)


def test_health_score_acotado_0_100():
    _reset(ingreso="120000")
    ins = _client().get("/api/insights").get_json()
    h = ins["health"]
    assert 0 <= h["score"] <= 100
    assert len(h["componentes"]) == 5
    assert all(0 <= c["pct"] <= 100 for c in h["componentes"])


# ---------------- runner sin pytest ----------------

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
