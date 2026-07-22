"""Utilidades compartidas por los importadores."""

# Meses en español (nombres completos y abreviaturas). Fuente única para todos
# los parsers; las búsquedas siempre se hacen en minúsculas.
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
         "diciembre": 12, "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5,
         "jun": 6, "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10,
         "nov": 11, "dic": 12}


def money(s: str) -> float:
    """Importe con separador de miles → float: '1,234.56' → 1234.56.
    Punto único para cualquier ajuste de formato/locale a futuro."""
    return float(s.replace(",", ""))
