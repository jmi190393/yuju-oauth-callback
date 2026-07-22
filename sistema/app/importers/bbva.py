"""Importador BBVA Libretón (PDF). Clasifica CARGOS/ABONOS por posición x de columna.

Validado contra 7 estados reales 2026 — concilia al centavo con los totales oficiales.
"""
import re

import pdfplumber
from ._util import money

DATE_RE = re.compile(r"^\d{2}/[A-Z]{3}$")
AMOUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\.\d{2}$")
MONTHS = {"ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
          "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12}


def _group_lines(words, tol=3.5):
    out = []
    for w in sorted(words, key=lambda w: w["top"]):
        if out and abs(w["top"] - out[-1][-1]["top"]) <= tol:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(ws, key=lambda w: w["x0"]) for ws in out]


def _to_iso(ddmmm, period):
    d, mon = ddmmm.split("/")
    month = MONTHS[mon]
    y_start = int(period[0].split("/")[2])
    y_end = int(period[1].split("/")[2])
    m_start = int(period[0].split("/")[1])
    year = y_start if (y_start == y_end or month >= m_start) else y_end
    return f"{year:04d}-{month:02d}-{int(d):02d}"


def _iso_ddmmyyyy(s):
    d, m, y = s.split("/")
    return f"{y}-{m}-{d}"


def sniff(text: str) -> bool:
    return "BBVA" in text and ("Libret" in text or "Saldo Anterior" in text)


def parse(path: str) -> dict:
    movements = []
    period = None
    saldo_ini = saldo_fin = None
    with pdfplumber.open(path) as pdf:
        # UNA sola extracción de palabras por página; de ahí salen las columnas,
        # el texto para los encabezados y la clasificación de movimientos.
        pages_lines = [_group_lines(page.extract_words()) for page in pdf.pages]

        col_x = {}
        for lines in pages_lines:
            for ws in lines:
                for w in ws:
                    if w["text"] in ("CARGOS", "ABONOS") and w["text"] not in col_x:
                        col_x[w["text"]] = (w["x0"] + w["x1"]) / 2
            if len(col_x) == 2:
                break
        if len(col_x) < 2:
            raise ValueError("No parece un estado BBVA Libretón (sin columnas CARGOS/ABONOS)")
        split_ca = (col_x["CARGOS"] + col_x["ABONOS"]) / 2
        right_of_abonos = col_x["ABONOS"] + 45

        current = None
        for lines in pages_lines:
            text = "\n".join(" ".join(w["text"] for w in ws) for ws in lines)
            m = re.search(r"Periodo DEL (\d{2}/\d{2}/\d{4}) AL (\d{2}/\d{2}/\d{4})", text)
            if m:
                period = (m.group(1), m.group(2))
            m = re.search(r"Saldo Anterior ([\d,]+\.\d{2})", text)
            if m:
                saldo_ini = money(m.group(1))
            m = re.search(r"Saldo Final ([\d,]+\.\d{2})", text)
            if m:
                saldo_fin = money(m.group(1))

            for ws in lines:
                texts = [w["text"] for w in ws]
                line = " ".join(texts)
                if line.startswith("Total de Movimientos"):
                    if current:
                        movements.append(current)
                        current = None
                    continue
                if len(ws) >= 3 and DATE_RE.match(texts[0]) and DATE_RE.match(texts[1]):
                    if current:
                        movements.append(current)
                    cargo = abono = None
                    desc_words = []
                    for w in ws[2:]:
                        t = w["text"]
                        cx = (w["x0"] + w["x1"]) / 2
                        if AMOUNT_RE.match(t):
                            if cx < split_ca:
                                cargo = t
                            elif cx < right_of_abonos:
                                abono = t
                        else:
                            desc_words.append(t)
                    current = {"fecha": texts[0], "descripcion": " ".join(desc_words),
                               "cargo": cargo, "abono": abono, "detalle": []}
                elif current is not None:
                    if any(s in line for s in ("PAGINA", "BBVA MEXICO, S.A.", "Estado de Cuenta",
                                               "No. de Cuenta", "No. de Cliente", "Av. Paseo")):
                        continue
                    if line.startswith("La GAT Real"):
                        continue
                    current["detalle"].append(line)
        if current:
            movements.append(current)

    if not period:
        raise ValueError("No encontré el periodo del estado BBVA")

    txns = []
    t_cargos = t_abonos = 0.0
    for m in movements:
        amount = m["cargo"] or m["abono"]
        if not amount:
            continue
        val = money(amount)
        direction = "cargo" if m["cargo"] else "abono"
        if direction == "cargo":
            t_cargos += val
        else:
            t_abonos += val
        txns.append({
            "date": _to_iso(m["fecha"], period),
            "description": m["descripcion"],
            "amount": val,
            "direction": direction,
            "detail": " | ".join(m["detalle"])[:300],
        })

    # Conciliación contra saldos oficiales
    reconciled = None
    if saldo_ini is not None and saldo_fin is not None:
        reconciled = abs((saldo_ini + t_abonos - t_cargos) - saldo_fin) < 0.05

    return {
        "bank": "bbva",
        "account_hint": {"institution": "BBVA", "kind": "debito"},
        "period": (_iso_ddmmyyyy(period[0]), _iso_ddmmyyyy(period[1])),
        "transactions": txns,
        "msi_plans": [],
        "balance_final": saldo_fin,
        "reconciliation": {"ok": reconciled, "cargos": round(t_cargos, 2),
                           "abonos": round(t_abonos, 2),
                           "saldo_inicial": saldo_ini, "saldo_final": saldo_fin},
    }
