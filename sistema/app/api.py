"""API del sistema — Fase 1."""
import calendar
import hashlib
import json
import os
import tempfile
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import COOKIE, current_user, hash_password, make_token, verify_password
from .categorizer import categorize
from .db import get_db
from .importers import detect_and_parse
from .models import (Account, Category, Goal, ImportBatch, MsiPlan, Provision,
                     Setting, Subscription, Transaction, User)

router = APIRouter(prefix="/api")


# ---------- helpers ----------

def _setting(db, key, default=None):
    s = db.get(Setting, key)
    return s.value if s else default


def _tc_usd(db):
    return float(_setting(db, "tc_usd", "18.5"))


def _month_bounds(month: str):
    y, m = int(month[:4]), int(month[5:7])
    return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])


def _add_months(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7])
    total = y * 12 + (m - 1) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _plan_unpaid_months(plan: MsiPlan) -> list[tuple[str, float]]:
    """Meses (AAAA-MM) que aún debe este plan, con su mensualidad."""
    out = []
    for i in range(plan.payments_made, plan.months):
        out.append((_add_months(plan.first_month, i), plan.monthly_payment))
    return out


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


GASTO_KINDS = ("fijo", "variable", "aprovisionamiento")


# ---------- auth ----------

class LoginIn(BaseModel):
    user: str
    password: str


@router.post("/login")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    q = data.user.strip().lower()
    user = db.query(User).filter(
        (func.lower(User.email) == q) | (func.lower(User.name) == q)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    response.set_cookie(COOKIE, make_token(user.id), max_age=30 * 86400,
                        httponly=True, samesite="lax")
    return {"name": user.name, "must_change_password": user.must_change_password}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"name": user.name, "email": user.email,
            "must_change_password": user.must_change_password}


class PasswordIn(BaseModel):
    current: str
    new: str


@router.post("/password")
def change_password(data: PasswordIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(data.current, user.password_hash):
        raise HTTPException(400, "La contraseña actual no es correcta")
    if len(data.new) < 8:
        raise HTTPException(400, "La nueva contraseña debe tener al menos 8 caracteres")
    user.password_hash = hash_password(data.new)
    user.must_change_password = False
    db.commit()
    return {"ok": True}


# ---------- catálogos ----------

@router.get("/accounts")
def list_accounts(user: User = Depends(current_user), db: Session = Depends(get_db)):
    tc = _tc_usd(db)
    out = []
    for a in db.query(Account).order_by(Account.kind, Account.name):
        mxn = a.balance * (tc if a.currency == "USD" else 1)
        out.append({"id": a.id, "name": a.name, "institution": a.institution,
                    "kind": a.kind, "currency": a.currency, "last4": a.last4,
                    "cut_day": a.cut_day, "pay_day": a.pay_day,
                    "balance": a.balance, "balance_mxn": round(mxn, 2),
                    "balance_date": a.balance_date.isoformat() if a.balance_date else None,
                    "in_networth": a.in_networth, "active": a.active, "notes": a.notes})
    return out


class AccountPatch(BaseModel):
    balance: float | None = None
    balance_date: str | None = None
    active: bool | None = None
    notes: str | None = None


@router.patch("/accounts/{account_id}")
def patch_account(account_id: int, data: AccountPatch,
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.get(Account, account_id)
    if not a:
        raise HTTPException(404, "Cuenta no encontrada")
    if data.balance is not None:
        a.balance = data.balance
        a.balance_date = date.fromisoformat(data.balance_date) if data.balance_date else date.today()
    if data.active is not None:
        a.active = data.active
    if data.notes is not None:
        a.notes = data.notes
    db.commit()
    return {"ok": True}


@router.get("/categories")
def list_categories(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "emoji": c.emoji, "kind": c.kind,
             "monthly_budget": c.monthly_budget}
            for c in db.query(Category).order_by(Category.sort)]


class CategoryPatch(BaseModel):
    monthly_budget: float | None = None


@router.patch("/categories/{cat_id}")
def patch_category(cat_id: int, data: CategoryPatch,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(Category, cat_id)
    if not c:
        raise HTTPException(404, "Categoría no encontrada")
    c.monthly_budget = data.monthly_budget
    db.commit()
    return {"ok": True}


# ---------- transacciones ----------

@router.get("/transactions")
def list_transactions(month: str | None = None, account_id: int | None = None,
                      category_id: int | None = None, q: str | None = None,
                      tag: str | None = None, limit: int = 200,
                      user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Transaction)
    if month:
        start, end = _month_bounds(month)
        query = query.filter(Transaction.date >= start, Transaction.date <= end)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if q:
        query = query.filter(Transaction.description.ilike(f"%{q}%"))
    if tag:
        query = query.filter(Transaction.tags.ilike(f"%{tag}%"))
    txns = query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit).all()
    return [_txn_json(t) for t in txns]


class TxnIn(BaseModel):
    amount: float
    description: str = ""
    account_id: int | None = None
    category_id: int | None = None
    date: str | None = None
    direction: str = "cargo"
    tags: str = ""
    notes: str = ""


@router.post("/transactions")
def create_transaction(data: TxnIn, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    account_id = data.account_id
    if not account_id:  # captura rápida: default = efectivo
        cash = db.query(Account).filter(Account.kind == "efectivo").first()
        account_id = cash.id if cash else db.query(Account).first().id
    category_id = data.category_id
    tags = data.tags
    if not category_id and data.description:
        cat_name, auto_tags = categorize(data.description)
        if cat_name:
            cat = db.query(Category).filter(Category.name == cat_name).first()
            category_id = cat.id if cat else None
            tags = tags or auto_tags
    t = Transaction(
        account_id=account_id, date=date.fromisoformat(data.date) if data.date else date.today(),
        description=data.description or "Gasto", amount=abs(data.amount),
        direction=data.direction, category_id=category_id, tags=tags,
        source="manual", notes=data.notes, created_by=user.id)
    db.add(t)
    db.commit()
    return _txn_json(t)


class TxnPatch(BaseModel):
    category_id: int | None = None
    tags: str | None = None
    factura_status: str | None = None
    notes: str | None = None
    description: str | None = None
    amount: float | None = None
    date: str | None = None


@router.patch("/transactions/{txn_id}")
def patch_transaction(txn_id: int, data: TxnPatch, user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(404, "Movimiento no encontrado")
    for field in ("category_id", "tags", "factura_status", "notes", "description"):
        val = getattr(data, field)
        if val is not None:
            setattr(t, field, val)
    if data.amount is not None:
        t.amount = abs(data.amount)
    if data.date is not None:
        t.date = date.fromisoformat(data.date)
    db.commit()
    return _txn_json(t)


@router.delete("/transactions/{txn_id}")
def delete_transaction(txn_id: int, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(404, "Movimiento no encontrado")
    db.delete(t)
    db.commit()
    return {"ok": True}


# ---------- presupuesto: regla del sobrante ----------

@router.get("/budget")
def budget(month: str | None = None, user: User = Depends(current_user),
           db: Session = Depends(get_db)):
    month = month or date.today().strftime("%Y-%m")
    start, end = _month_bounds(month)
    ingreso = float(_setting(db, "ingreso_mensual", "0"))

    cats = db.query(Category).order_by(Category.sort).all()
    spent = dict(
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(Transaction.date >= start, Transaction.date <= end,
                Transaction.direction == "cargo")
        .group_by(Transaction.category_id).all())

    aprov_total = sum(p.annual_amount for p in db.query(Provision)) / 12

    msi_month = 0.0
    for plan in db.query(MsiPlan).filter(MsiPlan.status == "activo"):
        for m, pago in _plan_unpaid_months(plan):
            if m == month:
                msi_month += pago

    rows = []
    plan_fijos = plan_vars = 0.0
    gasto_real = 0.0
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
        pct = round(s / b * 100) if b else None
        rows.append({"id": c.id, "name": c.name, "emoji": c.emoji, "kind": c.kind,
                     "budget": b, "spent": round(s, 2), "pct": pct,
                     "estado": "ok" if not b or s <= 0.8 * b else ("alerta" if s <= b else "excedido")})

    sobrante_plan = ingreso - plan_fijos - aprov_total - msi_month - plan_vars
    sobrante_real = ingreso - gasto_real - msi_month
    return {
        "month": month, "ingreso": ingreso,
        "fijos_plan": round(plan_fijos, 2), "variables_plan": round(plan_vars, 2),
        "aprovisionamiento": round(aprov_total, 2), "msi_mes": round(msi_month, 2),
        "sobrante_plan": round(sobrante_plan, 2),
        "gasto_real": round(gasto_real, 2), "sobrante_real_proyectado": round(sobrante_real, 2),
        "categorias": rows,
    }


# ---------- MSI ----------

@router.get("/msi")
def msi(user: User = Depends(current_user), db: Session = Depends(get_db)):
    this_month = date.today().strftime("%Y-%m")
    plans = []
    flow: dict[str, float] = {}
    for p in db.query(MsiPlan).order_by(MsiPlan.status, MsiPlan.first_month):
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
    db.commit()
    months = [_add_months(this_month, i) for i in range(6)]
    return {
        "plans": plans,
        "committed_next_6": [{"month": m, "amount": round(flow.get(m, 0), 2)} for m in months],
        "total_pending": round(sum(p["pending"] for p in plans if p["status"] == "activo"), 2),
    }


class MsiIn(BaseModel):
    account_id: int
    merchant: str
    total_amount: float
    months: int
    first_month: str
    purchase_date: str | None = None
    payments_made: int = 0


@router.post("/msi")
def create_msi(data: MsiIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = MsiPlan(account_id=data.account_id, merchant=data.merchant,
                total_amount=data.total_amount, months=data.months,
                monthly_payment=round(data.total_amount / data.months, 2),
                payments_made=data.payments_made, first_month=data.first_month,
                purchase_date=date.fromisoformat(data.purchase_date) if data.purchase_date else None)
    db.add(p)
    db.commit()
    return {"id": p.id}


# ---------- suscripciones ----------

@router.get("/subscriptions")
def list_subs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    tc = _tc_usd(db)
    out = []
    annual_total = 0.0
    for s in db.query(Subscription).order_by(Subscription.status, Subscription.name):
        mxn = s.amount * (tc if s.currency == "USD" else 1)
        yearly = mxn * (12 if s.frequency == "mensual" else 1)
        if s.status == "activa":
            annual_total += yearly
        out.append({"id": s.id, "name": s.name, "amount": s.amount, "currency": s.currency,
                    "frequency": s.frequency, "status": s.status,
                    "account": s.account.name if s.account else None,
                    "next_renewal": s.next_renewal.isoformat() if s.next_renewal else None,
                    "annual_mxn": round(yearly, 2), "notes": s.notes})
    return {"subscriptions": out, "annual_total_mxn": round(annual_total, 2)}


class SubIn(BaseModel):
    name: str
    amount: float
    currency: str = "MXN"
    frequency: str = "mensual"
    account_id: int | None = None
    next_renewal: str | None = None
    notes: str = ""


@router.post("/subscriptions")
def create_sub(data: SubIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = Subscription(name=data.name, amount=data.amount, currency=data.currency,
                     frequency=data.frequency, account_id=data.account_id,
                     next_renewal=date.fromisoformat(data.next_renewal) if data.next_renewal else None,
                     notes=data.notes)
    db.add(s)
    db.commit()
    return {"id": s.id}


class SubPatch(BaseModel):
    status: str | None = None
    amount: float | None = None
    next_renewal: str | None = None
    notes: str | None = None


@router.patch("/subscriptions/{sub_id}")
def patch_sub(sub_id: int, data: SubPatch, user: User = Depends(current_user),
              db: Session = Depends(get_db)):
    s = db.get(Subscription, sub_id)
    if not s:
        raise HTTPException(404, "Suscripción no encontrada")
    if data.status is not None:
        s.status = data.status
    if data.amount is not None:
        s.amount = data.amount
    if data.next_renewal is not None:
        s.next_renewal = date.fromisoformat(data.next_renewal)
    if data.notes is not None:
        s.notes = data.notes
    db.commit()
    return {"ok": True}


# ---------- metas ----------

@router.get("/goals")
def list_goals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for g in db.query(Goal).order_by(Goal.id):
        out.append({"id": g.id, "name": g.name, "emoji": g.emoji,
                    "target_amount": g.target_amount, "current_amount": g.current_amount,
                    "pct": round(g.current_amount / g.target_amount * 100) if g.target_amount else 0,
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                    "notes": g.notes})
    return out


class GoalPatch(BaseModel):
    current_amount: float | None = None
    target_amount: float | None = None
    notes: str | None = None


@router.patch("/goals/{goal_id}")
def patch_goal(goal_id: int, data: GoalPatch, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    g = db.get(Goal, goal_id)
    if not g:
        raise HTTPException(404, "Meta no encontrada")
    if data.current_amount is not None:
        g.current_amount = data.current_amount
    if data.target_amount is not None:
        g.target_amount = data.target_amount
    if data.notes is not None:
        g.notes = data.notes
    db.commit()
    return {"ok": True}


class GoalIn(BaseModel):
    name: str
    emoji: str = "🎯"
    target_amount: float
    target_date: str | None = None
    notes: str = ""


@router.post("/goals")
def create_goal(data: GoalIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    g = Goal(name=data.name, emoji=data.emoji, target_amount=data.target_amount,
             target_date=date.fromisoformat(data.target_date) if data.target_date else None,
             notes=data.notes)
    db.add(g)
    db.commit()
    return {"id": g.id}


# ---------- dashboard: las 5 preguntas ----------

@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = date.today()
    month = today.strftime("%Y-%m")
    tc = _tc_usd(db)

    # 1. ¿Cuánto tengo? (líquido: débito + efectivo)
    liquid = sum(a.balance * (tc if a.currency == "USD" else 1)
                 for a in db.query(Account).filter(Account.kind.in_(("debito", "efectivo")),
                                                   Account.active))

    # 2. ¿Cómo voy este mes?
    b = budget(month, user, db)

    # 3. ¿Qué viene? (próximos 30 días)
    upcoming = []
    for a in db.query(Account).filter(Account.kind == "credito", Account.active):
        for label, day in (("Corte", a.cut_day), ("Pago", a.pay_day)):
            if not day:
                continue
            d = date(today.year, today.month, min(day, calendar.monthrange(today.year, today.month)[1]))
            if d < today:
                nm = _add_months(month, 1)
                d = date(int(nm[:4]), int(nm[5:7]), min(day, calendar.monthrange(int(nm[:4]), int(nm[5:7]))[1]))
            if (d - today).days <= 30:
                upcoming.append({"date": d.isoformat(), "label": f"{label} {a.name}", "amount": None})
    for s in db.query(Subscription).filter(Subscription.status == "activa",
                                           Subscription.next_renewal.isnot(None)):
        if 0 <= (s.next_renewal - today).days <= 30:
            upcoming.append({"date": s.next_renewal.isoformat(),
                             "label": f"Renovación {s.name}",
                             "amount": s.amount * (tc if s.currency == "USD" else 1)})
    for plan in db.query(MsiPlan).filter(MsiPlan.status == "activo"):
        for m, pago in _plan_unpaid_months(plan):
            if m in (month, _add_months(month, 1)):
                upcoming.append({"date": f"{m}-01", "label": f"MSI {plan.merchant[:30]} ({plan.account.name})",
                                 "amount": pago})
    upcoming.sort(key=lambda x: x["date"])

    # 4. Metas
    goals = list_goals(user, db)

    # 5. ¿Cuánto valgo?
    networth = sum(a.balance * (tc if a.currency == "USD" else 1)
                   for a in db.query(Account).filter(Account.in_networth, Account.active))
    msi_pending = sum(sum(x[1] for x in _plan_unpaid_months(p))
                      for p in db.query(MsiPlan).filter(MsiPlan.status == "activo"))

    return {
        "hoy": today.isoformat(), "usuario": user.name,
        "cuanto_tengo": {"liquido": round(liquid, 2)},
        "como_voy": {"ingreso": b["ingreso"], "gasto_real": b["gasto_real"],
                     "sobrante_plan": b["sobrante_plan"],
                     "sobrante_real_proyectado": b["sobrante_real_proyectado"],
                     "msi_mes": b["msi_mes"],
                     "semaforo": "verde" if b["gasto_real"] <= 0.8 * (b["fijos_plan"] + b["variables_plan"] + b["aprovisionamiento"])
                     else ("amarillo" if b["sobrante_real_proyectado"] > 0 else "rojo")},
        "que_viene": upcoming[:10],
        "metas": goals,
        "cuanto_valgo": {"patrimonio_mxn": round(networth, 2),
                         "msi_pendiente": round(msi_pending, 2),
                         "tc_usd": tc},
    }


# ---------- importador ----------

@router.post("/import")
async def import_statement(file: UploadFile, user: User = Depends(current_user),
                           db: Session = Depends(get_db)):
    suffix = os.path.splitext(file.filename or "estado.pdf")[1] or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        parsed = detect_and_parse(tmp_path, file.filename or "estado.pdf")
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        os.unlink(tmp_path)

    # Resolver cuenta destino
    hint = parsed["account_hint"]
    account = None
    if parsed["bank"] == "amex" and hint.get("last4"):
        for a in db.query(Account).filter(Account.institution == "American Express"):
            if a.last4 and a.last4 in hint["last4"]:
                account = a
                break
    if account is None:
        account = db.query(Account).filter(
            Account.institution == hint["institution"], Account.kind == hint["kind"]).first()
    if account is None:
        raise HTTPException(400, f"No hay cuenta configurada para {hint['institution']} {hint['kind']}")

    cat_by_name = {c.name: c.id for c in db.query(Category)}
    n_new = n_skip = 0
    for t in parsed["transactions"]:
        key = _txn_key(account.id, t["date"], t["description"], t["amount"], t["direction"])
        if db.query(Transaction.id).filter(Transaction.external_key == key).first():
            n_skip += 1
            continue
        cat_name, tags = categorize(t["description"], t.get("detail", ""))
        db.add(Transaction(
            account_id=account.id, date=date.fromisoformat(t["date"]),
            description=t["description"], amount=t["amount"], direction=t["direction"],
            category_id=cat_by_name.get(cat_name), tags=tags, source="import",
            external_key=key, notes=t.get("detail", "")[:300], created_by=user.id))
        n_new += 1

    # Sincronizar planes MSI del estado
    n_msi = 0
    for p in parsed.get("msi_plans", []):
        pkey = hashlib.sha1(
            f"{account.id}|{p['merchant']}|{p.get('purchase_date')}|{p['total_amount']:.2f}|{p['months']}".encode()
        ).hexdigest()
        existing = db.query(MsiPlan).filter(MsiPlan.external_key == pkey).first()
        if existing:
            if p["payments_made"] > existing.payments_made:
                existing.payments_made = p["payments_made"]
                if existing.payments_made >= existing.months:
                    existing.status = "liquidado"
        else:
            if p.get("first_month"):
                first = p["first_month"]
            else:
                # Primera mensualidad: en Amex cae al corte del mes siguiente a
                # la compra; en Revolut la 1a va en el mismo corte de la compra.
                pm = p.get("purchase_date") or parsed["period"][1]
                first = _add_months(pm[:7], 1) if parsed["bank"] == "amex" else pm[:7]
            db.add(MsiPlan(
                account_id=account.id, merchant=p["merchant"],
                purchase_date=date.fromisoformat(p["purchase_date"]) if p.get("purchase_date") else None,
                total_amount=p["total_amount"], months=p["months"],
                monthly_payment=p["monthly_payment"], payments_made=p["payments_made"],
                first_month=first, external_key=pkey))
            n_msi += 1

    # Actualizar saldos con lo que trae el estado
    if parsed.get("balance_final") is not None:
        account.balance = parsed["balance_final"]
        account.balance_date = date.fromisoformat(parsed["period"][1])
    if parsed.get("fondo_inversion_saldo") is not None:
        inv = db.query(Account).filter(Account.name == "Revolut Inversión").first()
        if inv:
            inv.balance = parsed["fondo_inversion_saldo"]
            inv.balance_date = date.fromisoformat(parsed["period"][1]) if parsed["period"][1] else date.today()

    rec = parsed.get("reconciliation", {})
    batch = ImportBatch(
        filename=file.filename or "estado", bank=parsed["bank"], account_id=account.id,
        period_start=date.fromisoformat(parsed["period"][0]) if parsed["period"][0] else None,
        period_end=date.fromisoformat(parsed["period"][1]) if parsed["period"][1] else None,
        n_imported=n_new, n_skipped=n_skip, reconciled=rec.get("ok"),
        summary=json.dumps(rec))
    db.add(batch)
    db.commit()

    return {"bank": parsed["bank"], "account": account.name,
            "period": parsed["period"], "imported": n_new, "skipped": n_skip,
            "msi_plans_new": n_msi, "reconciled": rec.get("ok"), "reconciliation": rec,
            "pago_requerido": parsed.get("pago_requerido"),
            "fecha_limite": parsed.get("fecha_limite")}


@router.post("/recategorize")
def recategorize(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Re-aplica las reglas a los movimientos sin categoría (tras mejorar reglas)."""
    cat_by_name = {c.name: c.id for c in db.query(Category)}
    n = 0
    for t in db.query(Transaction).filter(Transaction.category_id.is_(None)):
        cat_name, tags = categorize(t.description, t.notes or "")
        if cat_name:
            t.category_id = cat_by_name.get(cat_name)
            t.tags = t.tags or tags
            n += 1
    db.commit()
    return {"recategorized": n}


@router.get("/imports")
def list_imports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": b.id, "filename": b.filename, "bank": b.bank,
             "period": [b.period_start.isoformat() if b.period_start else None,
                        b.period_end.isoformat() if b.period_end else None],
             "imported": b.n_imported, "skipped": b.n_skipped,
             "reconciled": b.reconciled,
             "created_at": b.created_at.isoformat()}
            for b in db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(50)]
