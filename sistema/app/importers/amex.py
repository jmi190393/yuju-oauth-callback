"""Importador American Express México (Gold y Platinum, PDF).

Validado contra 10 estados reales 2026 — concilia contra el resumen oficial
(saldo anterior − pagos + cargos = saldo al corte) y extrae el portafolio
completo de planes de pagos diferidos / MSI.
"""
import re

import pdfplumber
from ._util import MESES, money

AMT = r"[\d,]+\.\d{2}"
TXN_RE = re.compile(rf"^(\d{{1,2}}) de\s?(\w+) (.+?) ({AMT})( CR)?$")
CARGO_RE = re.compile(r"^CARGO (\d+) DE\s?(\d+)$")
PLAN_RE = re.compile(
    rf"^(.+?)\s?(\d{{1,2}}) de\s?(\w{{3}}) ({AMT}) ([\d.]+)% ({AMT}) (\d+) de\s?(\d+) ({AMT})$")


def _mes(nombre):
    return MESES[nombre.lower()]


def sniff(text: str) -> bool:
    return "American Express" in text and "Período de Facturación" in text


def parse(path: str) -> dict:
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    info = {}
    m = re.search(r"(\d{4}-\d{6}-\d{5})", text)
    info["cuenta"] = m.group(1) if m else "?"
    m = re.search(
        r"Período de Facturación Del\s?(\d{1,2}) de\s?(\w+) al\s?(\d{1,2}) de\s?(\w+) de\s?(\d{4})", text)
    if not m:
        raise ValueError("No parece un estado Amex (sin período de facturación)")
    d1, mo1, d2, mo2, y = m.groups()
    y = int(y)
    m1n, m2n = _mes(mo1), _mes(mo2)
    y1 = y if m1n <= m2n else y - 1
    info["periodo"] = (f"{y1}-{m1n:02d}-{int(d1):02d}", f"{y}-{m2n:02d}-{int(d2):02d}")

    m = re.search(rf"({AMT})( CR)? - ({AMT}) \+ ({AMT}) = ({AMT})( CR)? ({AMT})( CR)?( {AMT})?", text)
    e_abonos = money(m.group(3)) if m else 0.0
    e_cargos = money(m.group(4)) if m else 0.0
    saldo_corte = (("-" if m.group(6) else "") + m.group(5)).replace(",", "") if m else None

    year_end = y
    month_end = m2n

    def fecha_iso(d, mes_nombre):
        mn = _mes(mes_nombre)
        yy = year_end if mn <= month_end else year_end - 1
        return f"{yy}-{mn:02d}-{int(d):02d}"

    txns, plans = [], []
    in_plans = False
    current = None
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith(("Resumen de Planes de Pagos Diferidos",
                            "Resumen de Meses sin Intereses")):
            in_plans = True
        if line.startswith(("Totales de Planes", "Total de Plan de Meses", "Fecha y Detalle")):
            in_plans = False
        if in_plans:
            pm = PLAN_RE.match(line)
            if pm:
                pd_d, pd_m = int(pm.group(2)), _mes(pm.group(3))
                pd_y = year_end if pd_m <= month_end else year_end - 1
                plans.append({
                    "merchant": pm.group(1).strip(),
                    "purchase_date": f"{pd_y}-{pd_m:02d}-{pd_d:02d}",
                    "total_amount": money(pm.group(4)),
                    "pending": money(pm.group(6)),
                    "payments_made": int(pm.group(7)),
                    "months": int(pm.group(8)),
                    "monthly_payment": money(pm.group(9)),
                })
            continue
        tm = TXN_RE.match(line)
        # El grupo 2 es \w+ (no valida mes): si no es un mes real, no es una
        # transacción → se trata como continuación en vez de reventar en _mes().
        if tm and "Página" not in line and tm.group(2).lower() in MESES:
            if current:
                txns.append(current)
            current = {
                "date": fecha_iso(tm.group(1), tm.group(2)),
                "description": tm.group(3).strip(),
                "amount": money(tm.group(4)),
                "direction": "abono" if tm.group(5) else "cargo",
                "detail": "",
            }
        elif current is not None:
            cm = CARGO_RE.match(line)
            if cm:
                current["detail"] = f"MSI {cm.group(1)} de {cm.group(2)}"
            elif line == "CR":
                current["direction"] = "abono"
            elif line.startswith("RFC"):
                current["detail"] = (current["detail"] + " " + line[:60]).strip()
                if line.endswith("CR"):
                    current["direction"] = "abono"
    if current:
        txns.append(current)

    # Algunos estados (p.ej. Platinum con MSI automático) NO traen la sección
    # "Resumen de Planes": el plan solo se ve como transacción "CARGO N DE M".
    # En ese caso derivamos el plan desde la transacción.
    if not plans:
        seen = set()
        for t in txns:
            m = re.match(r"MSI (\d+) de (\d+)", t.get("detail", ""))
            if not m or t["direction"] != "cargo":
                continue
            n, total_m = int(m.group(1)), int(m.group(2))
            key = (t["description"], t["amount"], total_m)
            if key in seen:
                continue
            seen.add(key)
            ty, tm = int(t["date"][:4]), int(t["date"][5:7])
            first_idx = ty * 12 + (tm - 1) - (n - 1)
            plans.append({
                "merchant": t["description"],
                "purchase_date": None,
                "total_amount": round(t["amount"] * total_m, 2),
                "pending": round(t["amount"] * (total_m - n), 2),
                "payments_made": n,
                "months": total_m,
                "monthly_payment": t["amount"],
                "first_month": f"{first_idx // 12:04d}-{first_idx % 12 + 1:02d}",
            })

    t_c = sum(t["amount"] for t in txns if t["direction"] == "cargo")
    t_a = sum(t["amount"] for t in txns if t["direction"] == "abono")

    return {
        "bank": "amex",
        "account_hint": {"institution": "American Express", "kind": "credito",
                         "last4": info["cuenta"][-5:]},
        "period": info["periodo"],
        "transactions": txns,
        "msi_plans": plans,
        "saldo_corte": saldo_corte,
        "reconciliation": {"ok": abs(t_c - e_cargos) < 0.02 and abs(t_a - e_abonos) < 0.02,
                           "cargos": round(t_c, 2), "cargos_oficial": e_cargos,
                           "abonos": round(t_a, 2), "abonos_oficial": e_abonos},
    }
