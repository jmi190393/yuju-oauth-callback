"""Utilidades compartidas por los importadores."""


def money(s: str) -> float:
    """Importe con separador de miles → float: '1,234.56' → 1234.56.
    Punto único para cualquier ajuste de formato/locale a futuro."""
    return float(s.replace(",", ""))
