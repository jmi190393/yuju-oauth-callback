"""Detección automática de banco y despacho al parser correcto."""
import pdfplumber

from . import amex, bbva, revolut


def detect_and_parse(path: str, filename: str) -> dict:
    """Detecta el tipo de documento (por contenido, no por nombre) y lo parsea."""
    if filename.lower().endswith(".csv"):
        with open(path, "rb") as f:
            content = f.read()
        head = content.decode("utf-8-sig", errors="replace")[:120]
        if revolut.sniff_debit_csv(head):
            return revolut.parse_debit_csv(content)
        raise ValueError("CSV no reconocido. Formatos soportados: export de cuenta Revolut.")

    if not filename.lower().endswith(".pdf"):
        raise ValueError("Formato no soportado — sube un PDF de estado de cuenta o CSV de Revolut.")

    with pdfplumber.open(path) as pdf:
        first_pages = "\n".join((p.extract_text() or "") for p in pdf.pages[:2])

    if amex.sniff(first_pages):
        return amex.parse(path)
    if revolut.sniff_credit(first_pages):
        return revolut.parse_credit(path)
    if bbva.sniff(first_pages):
        return bbva.parse(path)
    raise ValueError(
        "No reconocí el banco de este documento. Soportados hoy: BBVA Libretón, "
        "Revolut crédito (PDF) y débito (CSV), Amex Gold/Platinum.")
