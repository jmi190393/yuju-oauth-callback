"""API del sistema (Flask, WSGI puro) — Fase 1."""
import calendar
import hashlib
import json
import os
import tempfile
from datetime import date

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from .auth import (COOKIE, current_user_id, hash_password, login_required,
                   make_token, verify_password)
from .categorizer import categorize, normalize
from .importers import detect_and_parse
from .models import (Account, Category, Goal, ImportBatch, MsiPlan, Provision,
                     Rule, Setting, Subscription, Transaction, User)

bp = Blueprint("api", __name__, url_prefix="/api")

APP_VERSION = "1.2"
GASTO_KINDS = ("fijo", "variable", "aprovisionamiento")


@bp.get("/version")
@login_required
def version():
    return jsonify({"version": APP_VERSION})


# ---------- helpers ----------

def db():
    return g.db


def body():
    return request.get_json(silent=True) or {}


def err(msg, code=400):
    return jsonify({"detail": msg}), code


def _setting(key, default=None):
    s = db().get(Setting, key)
    return s.value if s else default


def _tc_usd():
    return float(_setting("tc_usd", "18.5"))


def to_mxn(amount, currency, tc):
    """Convierte a MXN; los saldos/importes en USD usan el tipo de cambio."""
    return amount * (tc if currency == "USD" else 1)


def _learned_rules():
    """(pattern, category_id) de las reglas aprendidas del usuario."""
    return [(r.pattern, r.category_id) for r in db().query(Rule)]


def _resolve_category(desc, detail, cat_by_name, learned):
    """Categoría de un movimiento: reglas aprendidas (ganan) → reglas base."""
    norm = normalize(desc)
    for pat, cid in learned:
        if pat and pat in norm:
            return cid, ""
    name, tags = categorize(desc, detail)
    return cat_by_name.get(name), tags


def _month_bounds(month: str):
    y, m = int(month[:4]), int(month[5:7])
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def _add_months(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7])
    total = y * 12 + (m - 1) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _plan_unpaid_months(plan: MsiPlan):
    return [(_add_months(plan.first_month, i), plan.monthly_payment)
            for i in range(plan.payments_made, plan.months)]


def _txn_key(account_id, d, desc, amount, direction):
    raw = f"{account_id}|{d}|{desc}|{amount:.2f}|{direction}"
    return hashlib.sha1(raw.encode()).hexdigest()


def _txn_json(t: Transaction):
    return {
        "id": t.id, "date": t.date.isoformat(), "description": t.description,
        "amount": t.amount, "direction": t.direction,
        "account_id": t.account_id, "account": t.account.name if t.account else None,
        "category_id": t.category_id,
        "category": t.category.name if t.category else None,
        "category_emoji": t.category.emoji if t.category else "❓",
        "tags": t.tags, "source": t.source, "factura_status": t.factura_status,
        "notes": t.notes,
    }


# ---------- auth ----------

@bp.post("/login")
def login():
    data = body()
    q = str(data.get("user", "")).strip().lower()
    user = db().query(User).filter(
        (func.lower(User.email) == q) | (func.lower(User.name) == q)).first()
    if not user or not verify_password(data.get("password", ""), user.password_hash):
        return err("Usuario o contraseña incorrectos", 401)
    resp = jsonify({"name": user.name, "must_change_password": user.must_change_password})
    resp.set_cookie(COOKIE, make_token(user.id), max_age=30 * 86400,
                    httponly=True, samesite="Lax")
    return resp


@bp.post("/logout")
def logout():
    resp = jsonify({"ok": True})
    resp.delete_cookie(COOKIE)
    return resp


@bp.get("/me")
@login_required
def me():
    return jsonify({"name": g.user.name, "email": g.user.email,
                    "must_change_password": g.user.must_change_password})


@bp.post("/password")
@login_required
def change_password():
    data = body()
    if not verify_password(data.get("current", ""), g.user.password_hash):
        return err("La contraseña actual no es correcta")
    if len(data.get("new", "")) < 8:
        return err("La nueva contraseña debe tener al menos 8 caracteres")
    g.user.password_hash = hash_password(data["new"])
    g.user.must_change_password = False
    db().commit()
    return jsonify({"ok": True})


# ---------- catálogos ----------

@bp.get("/accounts")
@login_required
def list_accounts():
    tc = _tc_usd()
    out = []
    for a in db().query(Account).order_by(Account.kind, Account.name):
        mxn = to_mxn(a.balance, a.currency, tc)
        out.append({"id": a.id, "name": a.name, "institution": a.institution,
                    "kind": a.kind, "currency": a.currency, "last4": a.last4,
                    "cut_day": a.cut_day, "pay_day": a.pay_day,
                    "balance": a.balance, "balance_mxn": round(mxn, 2),
                    "balance_date": a.balance_date.isoformat() if a.balance_date else None,
                    "in_networth": a.in_networth, "active": a.active, "notes": a.notes})
    return jsonify(out)


@bp.patch("/accounts/<int:account_id>")
@login_required
def patch_account(account_id):
    a = db().get(Account, account_id)
    if not a:
        return err("Cuenta no encontrada", 404)
    data = body()
    if data.get("balance") is not None:
        a.balance = data["balance"]
        a.balance_date = date.fromisoformat(data["balance_date"]) if data.get("balance_date") else date.today()
    if data.get("active") is not None:
        a.active = data["active"]
    if data.get("notes") is not None:
        a.notes = data["notes"]
    db().commit()
    return jsonify({"ok": True})


@bp.get("/categories")
@login_required
def list_categories():
    return jsonify([{"id": c.id, "name": c.name, "emoji": c.emoji, "kind": c.kind,
                     "monthly_budget": c.monthly_budget}
                    for c in db().query(Category).order_by(Category.sort)])


@bp.patch("/categories/<int:cat_id>")
@login_required
def patch_category(cat_id):
    c = db().get(Category, cat_id)
    if not c:
        return err("Categoría no encontrada", 404)
    c.monthly_budget = body().get("monthly_budget")
    db().commit()
    return jsonify({"ok": True})


@bp.post("/categories")
@login_required
def create_category():
    """Crea una categoría nueva sobre la marcha (ej. desde 'Por catalogar')."""
    name = (body().get("name") or "").strip()
    if not name:
        return err("Escribe un nombre de categoría")
    existing = db().query(Category).filter(func.lower(Category.name) == name.lower()).first()
    if existing:
        return jsonify({"id": existing.id, "name": existing.name,
                        "emoji": existing.emoji, "created": False})
    c = Category(name=name, emoji=body().get("emoji", "🏷️"),
                 kind=body().get("kind", "variable"),
                 monthly_budget=body().get("monthly_budget"), sort=50)
    db().add(c)
    db().commit()
    return jsonify({"id": c.id, "name": c.name, "emoji": c.emoji, "created": True})


@bp.delete("/categories/<int:cat_id>")
@login_required
def delete_category(cat_id):
    c = db().get(Category, cat_id)
    if not c:
        return err("Categoría no encontrada", 404)
    if db().query(Transaction.id).filter(Transaction.category_id == cat_id).first():
        return err("No se puede borrar: tiene movimientos asignados")
    db().query(Rule).filter(Rule.category_id == cat_id).delete()
    db().delete(c)
    db().commit()
    return jsonify({"ok": True})


@bp.post("/categories/cleanup")
@login_required
def cleanup_categories():
    """Elimina las categorías que no se usaron (0 movimientos), salvo las de
    ingreso/transferencia/inversión (estructurales)."""
    protected = ("ingreso", "transferencia", "inversion")
    used = {cid for (cid,) in db().query(Transaction.category_id)
            .filter(Transaction.category_id.isnot(None)).distinct()}
    borradas = []
    for c in db().query(Category):
        if c.id not in used and c.kind not in protected:
            db().query(Rule).filter(Rule.category_id == c.id).delete()
            borradas.append(c.name)
            db().delete(c)
    db().commit()
    return jsonify({"deleted": borradas, "count": len(borradas)})


# ---------- transacciones ----------

@bp.get("/transactions")
@login_required
def list_transactions():
    args = request.args
    query = db().query(Transaction).options(
        joinedload(Transaction.account), joinedload(Transaction.category))
    if args.get("month"):
        start, end = _month_bounds(args["month"])
        query = query.filter(Transaction.date >= start, Transaction.date <= end)
    if args.get("account_id"):
        query = query.filter(Transaction.account_id == int(args["account_id"]))
    if args.get("category_id"):
        query = query.filter(Transaction.category_id == int(args["category_id"]))
    if args.get("q"):
        query = query.filter(Transaction.description.ilike(f"%{args['q']}%"))
    if args.get("tag"):
        query = query.filter(Transaction.tags.ilike(f"%{args['tag']}%"))
    limit = int(args.get("limit", 200))
    txns = query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit).all()
    return jsonify([_txn_json(t) for t in txns])


@bp.post("/transactions")
@login_required
def create_transaction():
    data = body()
    account_id = data.get("account_id")
    if not account_id:
        cash = db().query(Account).filter(Account.kind == "efectivo").first()
        account_id = cash.id if cash else db().query(Account).first().id
    category_id = data.get("category_id")
    tags = data.get("tags", "")
    desc = data.get("description", "")
    if not category_id and desc:
        cat_by_name = {c.name: c.id for c in db().query(Category)}
        category_id, auto_tags = _resolve_category(desc, "", cat_by_name, _learned_rules())
        tags = tags or auto_tags
    t = Transaction(
        account_id=account_id,
        date=date.fromisoformat(data["date"]) if data.get("date") else date.today(),
        description=desc or "Gasto", amount=abs(float(data.get("amount", 0))),
        direction=data.get("direction", "cargo"), category_id=category_id, tags=tags,
        source="manual", notes=data.get("notes", ""), created_by=g.user.id)
    db().add(t)
    db().commit()
    return jsonify(_txn_json(t))


@bp.patch("/transactions/<int:txn_id>")
@login_required
def patch_transaction(txn_id):
    t = db().get(Transaction, txn_id)
    if not t:
        return err("Movimiento no encontrado", 404)
    data = body()
    for field in ("category_id", "tags", "factura_status", "notes", "description"):
        if field in data and data[field] is not None:
            setattr(t, field, data[field])
    if data.get("amount") is not None:
        t.amount = abs(float(data["amount"]))
    if data.get("date"):
        t.date = date.fromisoformat(data["date"])
    db().commit()
    return jsonify(_txn_json(t))


@bp.delete("/transactions/<int:txn_id>")
@login_required
def delete_transaction(txn_id):
    t = db().get(Transaction, txn_id)
    if not t:
        return err("Movimiento no encontrado", 404)
    db().delete(t)
    db().commit()
    return jsonify({"ok": True})


# ---------- presupuesto: regla del sobrante ----------

def _budget(month):
    start, end = _month_bounds(month)
    ingreso = float(_setting("ingreso_mensual", "0"))
    cats = db().query(Category).order_by(Category.sort).all()
    spent = dict(
        db().query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(Transaction.date >= start, Transaction.date <= end,
                Transaction.direction == "cargo")
        .group_by(Transaction.category_id).all())
    aprov_total = sum(p.annual_amount for p in db().query(Provision)) / 12
    msi_month = 0.0
    for plan in db().query(MsiPlan).filter(MsiPlan.status == "activo"):
        for m, pago in _plan_unpaid_months(plan):
            if m == month:
                msi_month += pago
    rows = []
    plan_fijos = plan_vars = gasto_real = 0.0
    for c in cats:
        if c.kind not in GASTO_KINDS:
            continue
        s = float(spent.get(c.id) or 0)
        b = c.monthly_budget or 0
        if c.kind == "fijo":
            plan_fijos += b
        elif c.kind == "variable":
            plan_vars += b
        gasto_real += s
        rows.append({"id": c.id, "name": c.name, "emoji": c.emoji, "kind": c.kind,
                     "budget": b, "spent": round(s, 2),
                     "pct": round(s / b * 100) if b else None,
                     "estado": "ok" if not b or s <= 0.8 * b else ("alerta" if s <= b else "excedido")})
    sobrante_plan = ingreso - plan_fijos - aprov_total - msi_month - plan_vars
    sobrante_real = ingreso - gasto_real - msi_month
    return {
        "month": month, "ingreso": ingreso,
        "fijos_plan": round(plan_fijos, 2), "variables_plan": round(plan_vars, 2),
        "aprovisionamiento": round(aprov_total, 2), "msi_mes": round(msi_month, 2),
        "sobrante_plan": round(sobrante_plan, 2), "gasto_real": round(gasto_real, 2),
        "sobrante_real_proyectado": round(sobrante_real, 2), "categorias": rows,
    }


@bp.get("/budget")
@login_required
def budget():
    return jsonify(_budget(request.args.get("month") or date.today().strftime("%Y-%m")))


# ---------- MSI ----------

@bp.get("/msi")
@login_required
def msi():
    this_month = date.today().strftime("%Y-%m")
    plans, flow = [], {}
    for p in db().query(MsiPlan).order_by(MsiPlan.status, MsiPlan.first_month):
        unpaid = _plan_unpaid_months(p) if p.status == "activo" else []
        pending = round(sum(x[1] for x in unpaid), 2)
        if p.status == "activo" and not unpaid:
            p.status = "liquidado"
        for m, pago in unpaid:
            if m >= this_month:
                flow[m] = flow.get(m, 0) + pago
        plans.append({
            "id": p.id, "account": p.account.name, "merchant": p.merchant,
            "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
            "total_amount": p.total_amount, "months": p.months,
            "monthly_payment": p.monthly_payment, "payments_made": p.payments_made,
            "pending": pending, "status": p.status,
            "ends": _add_months(p.first_month, p.months - 1),
        })
    db().commit()
    months = [_add_months(this_month, i) for i in range(6)]
    return jsonify({
        "plans": plans,
        "committed_next_6": [{"month": m, "amount": round(flow.get(m, 0), 2)} for m in months],
        "total_pending": round(sum(p["pending"] for p in plans if p["status"] == "activo"), 2),
    })


@bp.post("/msi")
@login_required
def create_msi():
    data = body()
    p = MsiPlan(account_id=data["account_id"], merchant=data["merchant"],
                total_amount=data["total_amount"], months=data["months"],
                monthly_payment=round(data["total_amount"] / data["months"], 2),
                payments_made=data.get("payments_made", 0), first_month=data["first_month"],
                purchase_date=date.fromisoformat(data["purchase_date"]) if data.get("purchase_date") else None)
    db().add(p)
    db().commit()
    return jsonify({"id": p.id})


# ---------- suscripciones ----------

@bp.get("/subscriptions")
@login_required
def list_subs():
    tc = _tc_usd()
    out, annual_total = [], 0.0
    for s in db().query(Subscription).order_by(Subscription.status, Subscription.name):
        yearly = to_mxn(s.amount, s.currency, tc) * (12 if s.frequency == "mensual" else 1)
        if s.status == "activa":
            annual_total += yearly
        out.append({"id": s.id, "name": s.name, "amount": s.amount, "currency": s.currency,
                    "frequency": s.frequency, "status": s.status,
                    "account": s.account.name if s.account else None,
                    "next_renewal": s.next_renewal.isoformat() if s.next_renewal else None,
                    "annual_mxn": round(yearly, 2), "notes": s.notes})
    return jsonify({"subscriptions": out, "annual_total_mxn": round(annual_total, 2)})


@bp.post("/subscriptions")
@login_required
def create_sub():
    data = body()
    s = Subscription(name=data["name"], amount=data["amount"], currency=data.get("currency", "MXN"),
                     frequency=data.get("frequency", "mensual"), account_id=data.get("account_id"),
                     next_renewal=date.fromisoformat(data["next_renewal"]) if data.get("next_renewal") else None,
                     notes=data.get("notes", ""))
    db().add(s)
    db().commit()
    return jsonify({"id": s.id})


@bp.patch("/subscriptions/<int:sub_id>")
@login_required
def patch_sub(sub_id):
    s = db().get(Subscription, sub_id)
    if not s:
        return err("Suscripción no encontrada", 404)
    data = body()
    if data.get("status") is not None:
        s.status = data["status"]
    if data.get("amount") is not None:
        s.amount = data["amount"]
    if data.get("next_renewal") is not None:
        s.next_renewal = date.fromisoformat(data["next_renewal"])
    if data.get("notes") is not None:
        s.notes = data["notes"]
    db().commit()
    return jsonify({"ok": True})


# ---------- metas ----------

def _goals_list():
    out = []
    for gl in db().query(Goal).order_by(Goal.id):
        out.append({"id": gl.id, "name": gl.name, "emoji": gl.emoji,
                    "target_amount": gl.target_amount, "current_amount": gl.current_amount,
                    "pct": round(gl.current_amount / gl.target_amount * 100) if gl.target_amount else 0,
                    "target_date": gl.target_date.isoformat() if gl.target_date else None,
                    "notes": gl.notes})
    return out


@bp.get("/goals")
@login_required
def list_goals():
    return jsonify(_goals_list())


@bp.patch("/goals/<int:goal_id>")
@login_required
def patch_goal(goal_id):
    gl = db().get(Goal, goal_id)
    if not gl:
        return err("Meta no encontrada", 404)
    data = body()
    if data.get("current_amount") is not None:
        gl.current_amount = data["current_amount"]
    if data.get("target_amount") is not None:
        gl.target_amount = data["target_amount"]
    if data.get("notes") is not None:
        gl.notes = data["notes"]
    db().commit()
    return jsonify({"ok": True})


@bp.post("/goals")
@login_required
def create_goal():
    data = body()
    gl = Goal(name=data["name"], emoji=data.get("emoji", "🎯"), target_amount=data["target_amount"],
              target_date=date.fromisoformat(data["target_date"]) if data.get("target_date") else None,
              notes=data.get("notes", ""))
    db().add(gl)
    db().commit()
    return jsonify({"id": gl.id})


# ---------- dashboard: las 5 preguntas ----------

@bp.get("/dashboard")
@login_required
def dashboard():
    today = date.today()
    month = today.strftime("%Y-%m")
    tc = _tc_usd()

    liquid = sum(to_mxn(a.balance, a.currency, tc)
                 for a in db().query(Account).filter(Account.kind.in_(("debito", "efectivo")),
                                                     Account.active))
    b = _budget(month)

    upcoming = []
    for a in db().query(Account).filter(Account.kind == "credito", Account.active):
        for label, day in (("Corte", a.cut_day), ("Pago", a.pay_day)):
            if not day:
                continue
            d = date(today.year, today.month, min(day, calendar.monthrange(today.year, today.month)[1]))
            if d < today:
                nm = _add_months(month, 1)
                d = date(int(nm[:4]), int(nm[5:7]), min(day, calendar.monthrange(int(nm[:4]), int(nm[5:7]))[1]))
            if (d - today).days <= 30:
                upcoming.append({"date": d.isoformat(), "label": f"{label} {a.name}", "amount": None})
    for s in db().query(Subscription).filter(Subscription.status == "activa",
                                             Subscription.next_renewal.isnot(None)):
        if 0 <= (s.next_renewal - today).days <= 30:
            upcoming.append({"date": s.next_renewal.isoformat(),
                             "label": f"Renovación {s.name}",
                             "amount": to_mxn(s.amount, s.currency, tc)})
    for plan in db().query(MsiPlan).filter(MsiPlan.status == "activo"):
        for m, pago in _plan_unpaid_months(plan):
            if m in (month, _add_months(month, 1)):
                upcoming.append({"date": f"{m}-01",
                                 "label": f"MSI {plan.merchant[:30]} ({plan.account.name})",
                                 "amount": pago})
    upcoming.sort(key=lambda x: x["date"])

    networth = sum(to_mxn(a.balance, a.currency, tc)
                   for a in db().query(Account).filter(Account.in_networth, Account.active))
    msi_pending = sum(sum(x[1] for x in _plan_unpaid_months(p))
                      for p in db().query(MsiPlan).filter(MsiPlan.status == "activo"))
    por_catalogar = db().query(func.count(Transaction.id)).filter(
        Transaction.category_id.is_(None), Transaction.direction == "cargo").scalar() or 0
    umbral = 0.8 * (b["fijos_plan"] + b["variables_plan"] + b["aprovisionamiento"])
    return jsonify({
        "hoy": today.isoformat(), "usuario": g.user.name, "por_catalogar": por_catalogar,
        "cuanto_tengo": {"liquido": round(liquid, 2)},
        "como_voy": {"ingreso": b["ingreso"], "gasto_real": b["gasto_real"],
                     "sobrante_plan": b["sobrante_plan"],
                     "sobrante_real_proyectado": b["sobrante_real_proyectado"],
                     "msi_mes": b["msi_mes"],
                     "semaforo": "verde" if b["gasto_real"] <= umbral
                     else ("amarillo" if b["sobrante_real_proyectado"] > 0 else "rojo")},
        "que_viene": upcoming[:10],
        "metas": _goals_list(),
        "cuanto_valgo": {"patrimonio_mxn": round(networth, 2),
                         "msi_pendiente": round(msi_pending, 2), "tc_usd": tc},
    })


# ---------- importador ----------

@bp.post("/import")
@login_required
def import_statement():
    if "file" not in request.files:
        return err("No se recibió ningún archivo")
    upload = request.files["file"]
    filename = upload.filename or "estado.pdf"
    suffix = os.path.splitext(filename)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        upload.save(tmp.name)
        tmp_path = tmp.name
    try:
        parsed = detect_and_parse(tmp_path, filename)
    except ValueError as e:
        return err(str(e))
    finally:
        os.unlink(tmp_path)

    hint = parsed["account_hint"]
    account = None
    if parsed["bank"] == "amex" and hint.get("last4"):
        for a in db().query(Account).filter(Account.institution == "American Express"):
            if a.last4 and a.last4 in hint["last4"]:
                account = a
                break
    if account is None:
        account = db().query(Account).filter(
            Account.institution == hint["institution"], Account.kind == hint["kind"]).first()
    if account is None:
        return err(f"No hay cuenta configurada para {hint['institution']} {hint['kind']}")

    cat_by_name = {c.name: c.id for c in db().query(Category)}
    learned = _learned_rules()
    n_new = n_skip = 0
    for t in parsed["transactions"]:
        key = _txn_key(account.id, t["date"], t["description"], t["amount"], t["direction"])
        if db().query(Transaction.id).filter(Transaction.external_key == key).first():
            n_skip += 1
            continue
        category_id, tags = _resolve_category(t["description"], t.get("detail", ""), cat_by_name, learned)
        # Revolut crédito solo se usa en viajes (fuera de México): default = Viajes.
        if category_id is None and parsed["bank"] == "revolut_credito" and t["direction"] == "cargo":
            category_id, tags = cat_by_name.get("Viajes"), tags or "viaje"
        db().add(Transaction(
            account_id=account.id, date=date.fromisoformat(t["date"]),
            description=t["description"], amount=t["amount"], direction=t["direction"],
            category_id=category_id, tags=tags, source="import",
            external_key=key, notes=t.get("detail", "")[:300], created_by=g.user.id))
        n_new += 1

    n_msi = 0
    for p in parsed.get("msi_plans", []):
        pkey = hashlib.sha1(
            f"{account.id}|{p['merchant']}|{p.get('purchase_date')}|{p['total_amount']:.2f}|{p['months']}".encode()
        ).hexdigest()
        existing = db().query(MsiPlan).filter(MsiPlan.external_key == pkey).first()
        if existing:
            if p["payments_made"] > existing.payments_made:
                existing.payments_made = p["payments_made"]
                if existing.payments_made >= existing.months:
                    existing.status = "liquidado"
        else:
            if p.get("first_month"):
                first = p["first_month"]
            else:
                pm = p.get("purchase_date") or parsed["period"][1]
                first = _add_months(pm[:7], 1) if parsed["bank"] == "amex" else pm[:7]
            db().add(MsiPlan(
                account_id=account.id, merchant=p["merchant"],
                purchase_date=date.fromisoformat(p["purchase_date"]) if p.get("purchase_date") else None,
                total_amount=p["total_amount"], months=p["months"],
                monthly_payment=p["monthly_payment"], payments_made=p["payments_made"],
                first_month=first, external_key=pkey))
            n_msi += 1

    if parsed.get("balance_final") is not None:
        account.balance = parsed["balance_final"]
        account.balance_date = date.fromisoformat(parsed["period"][1])
    if parsed.get("fondo_inversion_saldo") is not None:
        inv = db().query(Account).filter(Account.name == "Revolut Inversión").first()
        if inv:
            inv.balance = parsed["fondo_inversion_saldo"]
            inv.balance_date = date.fromisoformat(parsed["period"][1]) if parsed["period"][1] else date.today()

    rec = parsed.get("reconciliation", {})
    db().add(ImportBatch(
        filename=filename, bank=parsed["bank"], account_id=account.id,
        period_start=date.fromisoformat(parsed["period"][0]) if parsed["period"][0] else None,
        period_end=date.fromisoformat(parsed["period"][1]) if parsed["period"][1] else None,
        n_imported=n_new, n_skipped=n_skip, reconciled=rec.get("ok"), summary=json.dumps(rec)))
    db().commit()

    return jsonify({"bank": parsed["bank"], "account": account.name,
                    "period": parsed["period"], "imported": n_new, "skipped": n_skip,
                    "msi_plans_new": n_msi, "reconciled": rec.get("ok"), "reconciliation": rec,
                    "pago_requerido": parsed.get("pago_requerido"),
                    "fecha_limite": parsed.get("fecha_limite")})


@bp.post("/recategorize")
@login_required
def recategorize():
    cat_by_name = {c.name: c.id for c in db().query(Category)}
    learned = _learned_rules()
    n = 0
    for t in db().query(Transaction).filter(Transaction.category_id.is_(None)):
        cid, tags = _resolve_category(t.description, t.notes or "", cat_by_name, learned)
        if cid:
            t.category_id = cid
            t.tags = t.tags or tags
            n += 1
    db().commit()
    return jsonify({"recategorized": n})


@bp.get("/uncategorized")
@login_required
def uncategorized():
    """Gastos sin categoría, agrupados por comercio (los de mayor monto primero).

    Solo cargos: es un sistema de gastos, los depósitos/transferencias entrantes
    no ensucian la cola. Se puede incluir todo con ?all=1.
    """
    query = db().query(Transaction.description, Transaction.direction,
                       func.count(Transaction.id), func.sum(Transaction.amount)) \
        .filter(Transaction.category_id.is_(None))
    if request.args.get("all") != "1":
        query = query.filter(Transaction.direction == "cargo")
    rows = (query.group_by(Transaction.description, Transaction.direction)
            .order_by(func.sum(Transaction.amount).desc()).all())
    return jsonify([{"description": d, "direction": dir_, "count": c, "total": round(t or 0, 2)}
                    for d, dir_, c, t in rows])


@bp.post("/categorize-merchant")
@login_required
def categorize_merchant():
    """Asigna categoría a TODOS los movimientos de un comercio y (opcional) la recuerda."""
    data = body()
    desc, cid = data.get("description"), data.get("category_id")
    if not desc or not cid:
        return err("Falta el comercio o la categoría")
    n = (db().query(Transaction)
         .filter(Transaction.category_id.is_(None), Transaction.description == desc)
         .update({"category_id": cid, "tags": data.get("tags", "")}, synchronize_session=False))
    if data.get("remember", True):
        pat = normalize(desc)
        rule = db().query(Rule).filter(Rule.pattern == pat).first()
        if rule:
            rule.category_id = cid
        else:
            db().add(Rule(pattern=pat, category_id=cid))
    db().commit()
    return jsonify({"updated": n})


@bp.get("/imports")
@login_required
def list_imports():
    return jsonify([{"id": b.id, "filename": b.filename, "bank": b.bank,
                     "period": [b.period_start.isoformat() if b.period_start else None,
                                b.period_end.isoformat() if b.period_end else None],
                     "imported": b.n_imported, "skipped": b.n_skipped,
                     "reconciled": b.reconciled, "created_at": b.created_at.isoformat()}
                    for b in db().query(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(50)])
