"""Categorización automática por reglas de contraparte/comercio.

Las reglas nacen del análisis real de los estados 2026 (docs 06–10 de la bóveda).
El sistema aprende: al corregir una categoría, se puede guardar una regla nueva
(tabla settings, clave rule:<patron>).
"""
import re

# (patrón regex sobre descripción en mayúsculas, nombre de categoría, tags)
RULES: list[tuple[str, str, str]] = [
    # Ingresos
    (r"BNET\b.*(NOMINA|PAGO)|NOMINA", "Nómina", ""),
    (r"WORTEV|IMPULSO EMPRENDIMIENTOS|WORLD WIDE TECH", "Rendimientos de inversión", ""),
    # Transferencias / movimientos internos (no son gasto)
    (r"REVOLUT|STP\b|ETORO|EToro|GBM|CETES|NAFIN|TRASPASO.*PROPIA", "Transferencia interna", ""),
    (r"MXN INVERSI|TO MXN|FROM MXN|ORDEN DE PAGO EXTRANJERO|SPEI ENVIADA? A BBVA", "Transferencia interna", ""),
    (r"MONTO A DIFERIR|MESES EN AUTOM", "Transferencia interna", ""),
    (r"PAGO TARJETA|PAGO TDC|PAGO DE TARJETA|GRACIAS POR SU PAGO|SU PAGO EN LINEA|BANAMEX.*PAGO|AMERICAN EXPRESS \d", "Pago de tarjeta", ""),
    (r"BANORTE", "Familia", ""),
    # Súper
    (r"LA COMER|TIENDA COM MEX|COSTCO|WAL.?MART|SORIANA|CHEDRAUI|SUPERAMA|7.?ELEVEN|OXXO", "Súper", ""),
    # Restaurantes y comida
    (r"UBER\s*EATS|RAPPI|DIDI FOOD", "Comida a domicilio", ""),
    (r"REST|TACOS|CAFE|STARBUCKS|SUSHI|PIZZA|BURGER|GRILL|COCINA|BISTRO", "Restaurantes", ""),
    # Auto
    (r"PASE\b|TAG\b|CAPUFE|AUTOPISTA", "Casetas", ""),
    (r"GASOLINER|PEMEX|G500|BP |SHELL|MOBIL|TESLA.*SUPERCHARG|SUPERCHARGER", "Gasolina y carga", ""),
    (r"QUALITAS|AUTO SEGURO", "Seguros", ""),
    (r"LAVADO|CAR WASH|ESTACIONAMIENTO|PARKING|PENSION AUTO", "Auto — otros", ""),
    # Salud
    (r"FARMACIA|SAN PABLO|GUADALAJARA FCIA|BENAVIDES", "Farmacia", ""),
    (r"BUPA|ZURICH|GNP|AXA|SEGURO.*GASTOS MEDICOS", "Seguros", ""),
    (r"NUTRAFOL", "Salud y cuidado personal", ""),
    (r"OPTICAS|OPTICA", "Salud y cuidado personal", ""),
    (r"CHARUA|HOSPITAL ANGELES|NIPT|GINECO|LABORATORIO|CLINICA", "Bebé y embarazo", "bebe"),
    (r"NANIT|BABY|BEBE", "Bebé y embarazo", "bebe"),
    (r"PSICOLOG|PABLO.*TERAPIA", "Salud y cuidado personal", ""),
    # Casa
    (r"SERENA 506|MANTENIMIENTO|ADMINISTRA", "Mantenimiento casa", ""),
    (r"CFE|COMISION FEDERAL", "Servicios casa", ""),
    (r"GAS NATURAL|NATURGY", "Servicios casa", ""),
    (r"OPD|AGUA HUIXQUILUCAN", "Servicios casa", ""),
    (r"H2OSYS|SOLUCIONES EN AGUA|MAIM", "Servicios casa", ""),
    (r"AT&T|ATT\b|TELMEX|TELCEL|IZZI|TOTALPLAY", "Internet y celular", ""),
    (r"IKEA|HOME DEPOT|LIVERPOOL HOGAR|SEARS HOGAR", "Hogar y muebles", ""),
    (r"ENRIQUE CRUZ", "Servicios profesionales", ""),
    (r"IVAN.*PASEO|KENAI|VETERINAR|PETCO|MASCOTA", "Mascota", ""),
    # Suscripciones
    (r"APPLE\.COM|APPLE COM BILL|ITUNES", "Suscripciones", ""),
    (r"CLAUDE|ANTHROPIC|OPENAI|CHATGPT|NETFLIX|SPOTIFY|DISNEY|AMAZON PRIME|PRIME VIDEO|OBSIDIAN|NINTENDO|HBO|MAX\b", "Suscripciones", ""),
    # Compras
    (r"AMAZON|MERCADOPAGO|MERCADO LIBRE|MELI|ISHOP|LIVERPOOL|PALACIO DE HIERRO|SEARS|ZARA|NORDSTROM|VUORI", "Compras", ""),
    # Viajes
    (r"KLM|AEROMEXICO|VOLARIS|VIVA ?AEROBUS|AIRBNB|BOOKING|EXPEDIA|MARRIOTT|HILTON|HYATT|ROYAL CARIBBEAN|DUTY FREE|ETA UK|AIRLINE|HOTEL", "Viajes", "viaje"),
    # Fiscal / gobierno
    (r"\bSAT\b|GOBIERNO|TESORERIA|PREDIAL|TENENCIA|VERIFICA", "Impuestos y gobierno", ""),
    # Efectivo
    (r"RETIRO SIN TARJETA|DISPOSICION.*EFECTIVO|CAJERO|ATM", "Efectivo", ""),
    # Comisiones
    (r"COMISION|IVA COMISION|ANUALIDAD|MEMBRESIA BANCARIA", "Comisiones bancarias", ""),
]

_COMPILED = [(re.compile(p), cat, tags) for p, cat, tags in RULES]


def normalize(s: str) -> str:
    """Clave de comercio: mayúsculas y espacios simples, para comparar reglas."""
    return " ".join((s or "").upper().split())


def categorize(description: str, detail: str = "") -> tuple[str | None, str]:
    """Devuelve (nombre_categoria, tags) o (None, '') según las reglas base."""
    text = f"{description} {detail}".upper()
    for rx, cat, tags in _COMPILED:
        if rx.search(text):
            return cat, tags
    return None, ""
