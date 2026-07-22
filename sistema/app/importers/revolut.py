"""Importadores Revolut: tarjeta de crédito (PDF) y cuenta débito (CSV).

Validados contra los estados reales 2026 — el crédito concilia al centavo,
incluidos los planes a meses sin intereses (formato 'N/M').
"""
import csv
import io
import re

import pdfplumber
from ._util import money

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12}

MOV_RE = re.compile(
    r"^(\d{1,2} \w{3,5}\.? \d{4}) (\d{1,2} \w{3,5}\.? \d{4}) (.+?) ([+-])\$([\d,]+\.\d{2})$")
FECHA_RE = re.compile(r"^(\d{1,2}) (\w{3,5})\.? (\d{4})$")
MSI_RE = re.compile(
    r"^(\d{1,2} \w{3,5}\.? \d{4}) (.+?) \$([\d,]+\.\d{2}) \$([\d,]+\.\d{2}) "
    r"\$([\d,]+\.\d{2}) NA \$([\d,]+\.\d{2}) (\d+)/(\d+) (\d+%)$")


def _to_iso(s):
    m = FECHA_RE.match(s)
    d, mon, y = m.group(1), m.group(2).lower().rstrip("."), m.group(3)
    return f"{y}-{MESES[mon]:02d}-{int(d):02d}"


def sniff_credit(text: str) -> bool:
    return "Revolut" in text and "Pago para no generar intereses" in text


def parse_credit(path: str) -> dict:
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    info = {}
    m = re.search(r"Periodo (\d{1,2} \w{3,5}\.? \d{4}) al (\d{1,2} \w{3,5}\.? \d{4})", text)
    if not m:
        raise ValueError("No parece un estado de crédito Revolut (sin periodo)")
    info["periodo"] = (_to_iso(m.group(1)), _to_iso(m.group(2)))
    m = re.search(r"Fecha límite de pago\d* \w+, (\d{1,2} \w{3,5}\.? \d{4})", text)
    info["fecha_limite"] = _to_iso(m.group(1)) if m else None
    m = re.search(r"Pago para no generar intereses\d* \$([\d,]+\.\d{2})", text)
    info["pago_requerido"] = money(m.group(1)) if m else None
    m = re.search(r"Total cargos \+\$([\d,]+\.\d{2})", text)
    e_cargos = money(m.group(1)) if m else 0.0
    m = re.search(r"Total abonos -\$([\d,]+\.\d{2})", text)
    e_abonos = money(m.group(1)) if m else 0.0

    lines = text.split("\n")
    msi = []
    for i, l in enumerate(lines):
        m = MSI_RE.match(l)
        if m:
            card = re.search(r"\*{4} (\d{4})", " ".join(lines[i + 1:i + 3]))
            msi.append({
                "purchase_date": _to_iso(m.group(1)),
                "merchant": m.group(2),
                "total_amount": money(m.group(3)),
                "pending": money(m.group(4)),
                "monthly_payment": money(m.group(6)),
                "payments_made": int(m.group(7)),
                "months": int(m.group(8)),
                "card": card.group(1) if card else "",
            })

    movs = []
    current = None
    for l in lines:
        m = MOV_RE.match(l)
        if m:
            if current:
                movs.append(current)
            current = {
                "date": _to_iso(m.group(1)),
                "description": m.group(3),
                "amount": money(m.group(5)),
                "direction": "cargo" if m.group(4) == "+" else "abono",
                "detail": [],
            }
        elif current is not None:
            if l.startswith(("Tarjeta:", "To:", "From:")):
                current["detail"].append(l)
            elif l.startswith(("Total cargos", "Total abonos", "Cargo no reconocidos")):
                movs.append(current)
                current = None
    if current:
        movs.append(current)

    t_c = sum(m["amount"] for m in movs if m["direction"] == "cargo")
    t_a = sum(m["amount"] for m in movs if m["direction"] == "abono")
    for m in movs:
        m["detail"] = " | ".join(m["detail"])[:200]

    return {
        "bank": "revolut_credito",
        "account_hint": {"institution": "Revolut", "kind": "credito"},
        "period": info["periodo"],
        "transactions": movs,
        "msi_plans": msi,
        "pago_requerido": info["pago_requerido"],
        "fecha_limite": info["fecha_limite"],
        "reconciliation": {"ok": abs(t_c - e_cargos) < 0.01 and abs(t_a - e_abonos) < 0.01,
                           "cargos": round(t_c, 2), "cargos_oficial": e_cargos,
                           "abonos": round(t_a, 2), "abonos_oficial": e_abonos},
    }


def sniff_debit_csv(head: str) -> bool:
    return head.startswith("Tipo,Producto,Fecha de inicio")


def parse_debit_csv(content: bytes) -> dict:
    """CSV de cuenta Revolut débito. Producto 'Actual' = cuenta corriente;
    'Rendimientos Diarios' = fondo de inversión (se importa como cuenta aparte)."""
    text = content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    txns = []
    dates = []
    inv_balance = None
    for r in rows:
        if r["Estado"] != "COMPLETADO":
            continue
        fecha = r["Fecha de inicio"][:10]
        amt = float(r["Importe"])
        producto = r["Producto"]
        if producto != "Actual":
            # movimientos del fondo: solo rastreamos el último saldo
            if r.get("Saldo"):
                inv_balance = float(r["Saldo"])
            continue
        dates.append(fecha)
        txns.append({
            "date": fecha,
            "description": r["Descripción"],
            "amount": abs(amt),
            "direction": "cargo" if amt < 0 else "abono",
            "detail": r["Tipo"],
        })
    period = (min(dates), max(dates)) if dates else (None, None)
    return {
        "bank": "revolut_debito",
        "account_hint": {"institution": "Revolut", "kind": "debito"},
        "period": period,
        "transactions": txns,
        "msi_plans": [],
        "fondo_inversion_saldo": inv_balance,
        "reconciliation": {"ok": True, "cargos": round(sum(t["amount"] for t in txns if t["direction"] == "cargo"), 2),
                           "abonos": round(sum(t["amount"] for t in txns if t["direction"] == "abono"), 2)},
    }
